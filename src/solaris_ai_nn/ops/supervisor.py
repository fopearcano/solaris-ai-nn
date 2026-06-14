"""OperationalSupervisor -- supervised, segmented, interruptible sessions.

Supervision strategy: the total bounded run is split into segments of
``healthcheck_interval_steps``. Each segment is a fresh runner continuing from
the same state directory (the Prompt-3 restart machinery makes this exact), and
**between** segments the supervisor runs the full ops loop: health check,
watchdog tick, budget check, incident logging, registry update, and (at the
end or on request) artifact rotation and safe shutdown. The existing runners
are not refactored; they are simply run in supervised slices.

Unbounded supervision requires ``continuous_explicit`` with explicit
acknowledgement in the manifest, and even then every segment remains bounded.
No OS services, no unmanaged background processes (the optional status server
is a managed daemon thread stopped in ``finalize``).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..governance import audit as GA
from ..governance.approval import APPROVED, ApprovalRegistry
from ..governance.audit import DEFAULT_GOVERNANCE_DIR, GovernanceAuditLog
from ..governance.checklists import post_run_checklist, pre_run_checklist
from ..governance.emergency import EmergencyStop
from ..governance.operator import OperatorSession
from ..governance.policy import GovernancePolicy, PolicyDecision
from ..governance.review import PostRunReview
from ..governance.risk import RiskAssessment, RiskLevel, assess_manifest
from ..utils.logging import get_logger
from . import incident as I
from . import watchdog as W
from .artifact_rotation import ArtifactRotationPolicy
from .health import HealthMonitor
from .incident import IncidentLog
from .local_status_server import LocalStatusServer
from .resource_budget import ResourceBudget, directory_bytes
from .run_manifest import OperationalRunManifest, RunMode
from .run_registry import RunRegistry
from .safe_shutdown import SafeShutdownManager
from .status import OperationalStatus
from .watchdog import Watchdog

logger = get_logger(__name__)

RunnerFactory = Callable[[OperationalRunManifest, int], Any]


def default_runner_factory(manifest: OperationalRunManifest,
                           segment_steps: int) -> Any:
    """Build the runner for one supervised segment, per manifest features."""
    if manifest.enabled_features.get("embodiment"):
        from ..embodiment.simulation_runner import SensorimotorSimulationRunner

        return SensorimotorSimulationRunner(
            max_steps=segment_steps, seed=manifest.seed,
            state_dir=manifest.state_dir, substrate=manifest.substrate,
            enable_language=manifest.enabled_features.get("language", False),
            enable_plasticity=manifest.enabled_features.get("plasticity", False))
    from ..runtime.continuous_runner import ContinuousRunner

    return ContinuousRunner(
        state_dir=manifest.state_dir, max_steps=segment_steps,
        checkpoint_interval_steps=manifest.checkpoint_interval_steps,
        heartbeat_interval_s=manifest.heartbeat_interval_s,
        seed=manifest.seed, substrate_name=manifest.substrate,
        enable_language=manifest.enabled_features.get("language", False),
        enable_plasticity=manifest.enabled_features.get("plasticity", False),
        plasticity_dry_run=manifest.enabled_features.get(
            "plasticity_dry_run", False),
        enable_latent=manifest.enabled_features.get("latent", False),
        allow_latent_plasticity=manifest.enabled_features.get(
            "latent_plasticity", False),
        enable_world_model=manifest.enabled_features.get("world_model",
                                                         False),
        enable_homeostasis=manifest.enabled_features.get("homeostasis",
                                                         False),
        enable_executive=manifest.enabled_features.get("executive", False),
        enable_ego=manifest.enabled_features.get("ego", False))


@dataclass
class OperationalSupervisor:
    """Runs and supervises one operational session."""

    manifest: OperationalRunManifest
    runner_factory: RunnerFactory = default_runner_factory
    dry_run: bool = False
    simulate_time: bool = False
    health_monitor: HealthMonitor = field(default_factory=HealthMonitor)
    budget: ResourceBudget = field(default_factory=ResourceBudget)
    registry: Optional[RunRegistry] = None
    # Governance (Prompt 12): on by default; pass governance_enabled=False
    # only for low-level tests of the bare supervision loop.
    governance_enabled: bool = True
    governance: Optional[GovernancePolicy] = None
    approvals: Optional[ApprovalRegistry] = None
    operator_session: Optional[OperatorSession] = None
    governance_dir: Optional[str] = None

    _stop_requested: bool = field(default=False, init=False)
    _segments_run: int = field(default=0, init=False)
    _last_health: Optional[Dict[str, Any]] = field(default=None, init=False)
    _last_runner: Any = field(default=None, init=False)
    _started_at: float = field(default=0.0, init=False)
    _finalized: bool = field(default=False, init=False)
    _governance_refused: bool = field(default=False, init=False)
    _refusal_reasons: List[str] = field(default_factory=list, init=False)
    _emergency_stop_triggered: bool = field(default=False, init=False)
    _policy_decision: Optional[PolicyDecision] = field(default=None,
                                                       init=False)
    _pre_run_checklist: Optional[Dict[str, Any]] = field(default=None,
                                                         init=False)
    _post_run_checklist: Optional[Dict[str, Any]] = field(default=None,
                                                          init=False)
    _post_run_review: Optional[Dict[str, Any]] = field(default=None,
                                                       init=False)
    _claim_guard_report: Optional[Dict[str, Any]] = field(default=None,
                                                          init=False)

    def __post_init__(self) -> None:
        m = self.manifest
        if m.mode == RunMode.CONTINUOUS_EXPLICIT \
                and not m.explicit_continuous_acknowledged:
            raise ValueError("unbounded supervision refused without explicit "
                             "acknowledgement")  # manifest also enforces this
        self.ops_dir = Path(m.artifact_dir) / "runs" / m.run_id
        self.ops_dir.mkdir(parents=True, exist_ok=True)
        if self.registry is None:
            self.registry = RunRegistry()  # default .solaris_ai_nn_runs path
        self.incidents = IncidentLog(self.ops_dir / "incidents.jsonl",
                                     run_id=m.run_id, session_id=m.session_id)
        self.watchdog = Watchdog(
            heartbeat_stale_s=max(60.0, m.heartbeat_interval_s * 30),
            checkpoint_stale_s=max(120.0, m.watchdog_interval_s * 60),
            max_duration_s=(None if self.simulate_time else m.max_duration_s))
        self.shutdown_manager = SafeShutdownManager(
            self.ops_dir, run_id=m.run_id, session_id=m.session_id)
        self.rotation = ArtifactRotationPolicy(
            directories=[m.state_dir, str(self.ops_dir)])
        self.status_server: Optional[LocalStatusServer] = None
        if m.enabled_features.get("local_status_server"):
            self.status_server = LocalStatusServer(provider=self._status_provider)
        # Governance wiring (Prompt 12). The emergency stop and its sentinel
        # exist even when governance is disabled -- it is always available.
        self.risk_assessment: Optional[RiskAssessment] = None
        self.gov_dir = Path(self.governance_dir or DEFAULT_GOVERNANCE_DIR)
        operator_name = (self.operator_session.operator.name
                         if self.operator_session is not None else "")
        if not self.governance_enabled:
            self.governance = None
            self.gov_audit = None
        else:
            self.gov_audit = GovernanceAuditLog(
                self.gov_dir / "governance_audit.jsonl",
                run_id=m.run_id, session_id=m.session_id,
                operator=operator_name)
            if self.approvals is None:
                self.approvals = ApprovalRegistry(
                    path=self.gov_dir / "approvals.json",
                    audit=self.gov_audit)
            elif self.approvals.audit is None:
                self.approvals.audit = self.gov_audit
            if self.governance is None:
                self.governance = GovernancePolicy(approvals=self.approvals,
                                                   audit=self.gov_audit)
            else:
                if self.governance.approvals is None:
                    self.governance.approvals = self.approvals
                if self.governance.audit is None:
                    self.governance.audit = self.gov_audit
        self.emergency = EmergencyStop(state_dir=m.state_dir,
                                       audit=self.gov_audit)
        self._write_json(self.ops_dir / "manifest.json", m.to_dict())

    # -- main loop ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Run the supervised session; returns the final status dict."""
        m = self.manifest
        self._started_at = time.time()
        self.registry.register_start(m)

        if self.governance is not None:
            allowed, reasons = self._governance_pre_run()
            if not allowed:
                self._governance_refused = True
                self._refusal_reasons = reasons
                status = self._build_status()
                self.finalize(graceful=True,
                              note="governance refused: " + "; ".join(reasons))
                return status.to_dict()

        if self.status_server is not None:
            self.status_server.start()

        if self.dry_run:
            status = self._build_status()
            self.finalize(graceful=True, note="dry run: nothing executed")
            return status.to_dict()

        total = m.max_steps if m.max_steps is not None else 0
        unbounded = m.mode == RunMode.CONTINUOUS_EXPLICIT and total == 0
        chunk = max(1, m.healthcheck_interval_steps)
        done = 0
        try:
            while not self._stop_requested:
                if not unbounded and done >= total:
                    break
                segment = chunk if unbounded else min(chunk, total - done)
                failed = False
                try:
                    runner = self.runner_factory(m, segment)
                    self._last_runner = runner
                    runner.run()
                except Exception as exc:
                    failed = True
                    self.incidents.record(
                        I.CHECKPOINT_FAILURE, "critical",
                        f"segment {self._segments_run + 1} failed: {exc}",
                        suggested_debug_step="re-run the segment with the "
                                             "same seed and inspect the trace")
                done += segment
                self._segments_run += 1
                self._supervise(segment_failed=failed)
        finally:
            self.finalize(graceful=True)
        return self._build_status().to_dict()

    def _supervise(self, segment_failed: bool = False) -> None:
        """Health + watchdog + budget between segments; act on decisions."""
        m = self.manifest

        # Emergency stop sentinel: an operator (or another process) created
        # <state_dir>/EMERGENCY_STOP -- request a safe shutdown now.
        if self.emergency.sentinel_present() \
                and not self._emergency_stop_triggered:
            self._emergency_stop_triggered = True
            self.incidents.record(
                I.EMERGENCY_STOP, "critical",
                "emergency stop sentinel file detected: "
                f"{self.emergency.sentinel}",
                suggested_debug_step="read the sentinel file and the "
                                     "governance audit for the reason")
            if self.gov_audit is not None:
                self.gov_audit.record(
                    GA.EMERGENCY_STOP_REQUESTED, decision="requested",
                    reason="sentinel file detected during supervised run",
                    metadata={"sentinel": str(self.emergency.sentinel)})
            self.shutdown_manager.request_shutdown(
                "emergency stop sentinel detected")
            self._stop_requested = True

        snapshot = self._health_snapshot()
        report = self.health_monitor.check(snapshot)
        self._last_health = report.to_dict()
        self._append_jsonl(self.ops_dir / "health.jsonl", self._last_health)
        if report.level == "warning":
            self.incidents.record(I.HEALTH_WARNING, "warning",
                                  "; ".join(c.detail for c in report.issues()),
                                  related_metric="health")
        elif report.level == "critical":
            self.incidents.record(I.HEALTH_CRITICAL, "critical",
                                  "; ".join(c.detail for c in report.issues()),
                                  related_metric="health",
                                  suggested_debug_step="see health.jsonl")

        # Latent monitoring: stuck cycles, dream-trace growth, Mysterium
        # runaway (Prompt 14). Decisions only; the watchdog acts below.
        latent = snapshot.get("latent") or {}
        if latent:
            stuck_after = max(60.0, m.watchdog_interval_s * 30)
            if latent.get("mode") not in ("awake", "quiet", None) \
                    and float(latent.get("mode_duration_s", 0.0) or 0.0) \
                    > stuck_after:
                self.incidents.record(
                    I.LATENT_CYCLE_STUCK, "critical",
                    f"latent mode {latent['mode']!r} has lasted "
                    f"{latent['mode_duration_s']:.0f}s",
                    related_metric="latent_mode_duration",
                    suggested_debug_step="wake the cycle; check the latent "
                                         "scheduler bounds")
                self.shutdown_manager.request_shutdown(
                    "latent cycle appears stuck")
                self._stop_requested = True
            if int(latent.get("dream_trace_count", 0) or 0) > 10_000:
                self.incidents.record(
                    I.DREAM_TRACE_OVERGROWTH, "warning",
                    f"{latent['dream_trace_count']} dream traces recorded",
                    related_metric="dream_trace_count",
                    suggested_debug_step="rotate dream_traces.jsonl or "
                                         "lower the dream cadence")
            if float(latent.get("mysterium_pressure", 0.0) or 0.0) >= 0.95:
                self.incidents.record(
                    I.MYSTERIUM_RUNAWAY, "warning",
                    "unknown pressure is pinned near maximum",
                    related_metric="mysterium_pressure",
                    suggested_debug_step="inspect the mysterium reasons in "
                                         "the latent report")

        # Homeostasis monitoring (Prompt 16): pressure readings only; the
        # watchdog keeps all stop authority.
        homeostasis = snapshot.get("homeostasis") or {}
        if homeostasis:
            stale_after = max(120.0, m.watchdog_interval_s * 30)
            last_update = float(homeostasis.get("last_update_at", 0.0) or 0.0)
            if last_update and time.time() - last_update > stale_after:
                self.incidents.record(
                    I.HOMEOSTASIS_STUCK, "warning",
                    f"no homeostasis update for "
                    f"{time.time() - last_update:.0f}s",
                    related_metric="homeostasis_update",
                    suggested_debug_step="check the regulation interval")
            if float(homeostasis.get("dominant_need_intensity", 0.0)
                     or 0.0) >= 0.98:
                self.incidents.record(
                    I.RUNAWAY_NEED_PRESSURE, "warning",
                    f"need {homeostasis.get('dominant_need')!r} is pinned "
                    "at maximum intensity",
                    related_metric="need_pressure",
                    suggested_debug_step="read the homeostasis report's "
                                         "variable section")
            if int(homeostasis.get("suppressed_desire_count", 0) or 0) >= 25:
                self.incidents.record(
                    I.REPEATED_SUPPRESSED_DESIRES, "warning",
                    f"{homeostasis['suppressed_desire_count']} desire "
                    "candidates suppressed this run",
                    related_metric="suppressed_desires",
                    suggested_debug_step="inspect the conflict ledger; the "
                                         "configuration may be fighting "
                                         "itself")
            if homeostasis.get("action_implication") \
                    == "safe_shutdown_recommended":
                self.incidents.record(
                    I.AUTO_DETERMINATION_SHUTDOWN_RECOMMENDED, "warning",
                    "auto-determination recommends a safe shutdown "
                    "(recommendation only; the watchdog decides)",
                    related_metric="not_being_pressure",
                    suggested_debug_step="review the Being/Not-Being "
                                         "reasons in the homeostasis "
                                         "report")

        # Executive monitoring (Prompt 17): evidence only; the watchdog
        # keeps all stop authority.
        executive = snapshot.get("executive") or {}
        if executive:
            if int(executive.get("no_safe_action_count", 0) or 0) >= 5:
                self.incidents.record(
                    I.EXECUTIVE_NO_SAFE_ACTION, "warning",
                    f"{executive['no_safe_action_count']} arbitrations "
                    "found no safe candidate",
                    related_metric="no_safe_action",
                    suggested_debug_step="read the inhibition ledger in "
                                         "the executive report")
            if int(executive.get("inhibited_candidate_count", 0)
                   or 0) >= 50:
                self.incidents.record(
                    I.EXECUTIVE_REPEATED_INHIBITION, "warning",
                    f"{executive['inhibited_candidate_count']} candidates "
                    "inhibited this run",
                    related_metric="inhibition_count",
                    suggested_debug_step="the configuration may be "
                                         "fighting its own constraints")
            if int(executive.get("plans_rejected", 0) or 0) >= 5:
                self.incidents.record(
                    I.EXECUTIVE_PLAN_REJECTED, "warning",
                    f"{executive['plans_rejected']} plans rejected",
                    related_metric="plan_rejections",
                    suggested_debug_step="check plan templates against "
                                         "the active inhibitions")
            if int(executive.get("forced_emergency_total", 0) or 0) >= 1 \
                    and executive.get("mode") == "emergency":
                self.incidents.record(
                    I.EXECUTIVE_MODE_FORCED_EMERGENCY, "warning",
                    "the executive was forced into emergency mode",
                    related_metric="executive_mode",
                    suggested_debug_step="resolve the underlying ops "
                                         "condition; the executive cannot "
                                         "clear it")

        # Developmental monitoring (Prompt 21): evidence only.
        developmental = snapshot.get("developmental") or {}
        if developmental:
            memory_layers = developmental.get("memory_layers") or {}
            if memory_layers.get("over_budget"):
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    f"developmental memory layers over budget: "
                    f"{memory_layers['over_budget']}",
                    related_metric="memory_layer_budget",
                    suggested_debug_step="run consolidation; raw events "
                                         "must not grow forever")
            if int(developmental.get("stagnation_windows", 0) or 0) >= 5:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    "no structural change measured over a long period",
                    related_metric="stagnation_windows",
                    suggested_debug_step="review the growth monitor; "
                                         "stagnation is a finding, not "
                                         "an error")
            if developmental.get("drift_status") == "fast_warning":
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    "uncontrolled drift detected by the developmental "
                    "drift monitor",
                    related_metric="drift_velocity",
                    suggested_debug_step="compare drift reports; fast "
                                         "drift may need stabilization")
            proto = developmental.get("proto_language") or {}
            if proto:
                symbol_count = int(proto.get("symbol_count", 0) or 0)
                ambiguous = int(proto.get("ambiguous_symbol_count", 0)
                                or 0)
                if symbol_count > 500:
                    self.incidents.record(
                        I.HEALTH_WARNING, "warning",
                        f"symbol explosion: {symbol_count} proto-"
                        "symbols registered",
                        related_metric="proto_symbol_count",
                        suggested_debug_step="raise the emergence "
                                             "threshold; repetition "
                                             "should be earning names")
                if symbol_count >= 10 and ambiguous / max(
                        1, symbol_count) > 0.8:
                    self.incidents.record(
                        I.HEALTH_WARNING, "warning",
                        "proto-symbol ambiguity is dominating "
                        f"({ambiguous}/{symbol_count})",
                        related_metric="symbol_ambiguity",
                        suggested_debug_step="review grounding "
                                             "consistency; ambiguous "
                                             "signs stay ambiguous")
                if symbol_count >= 20 \
                        and not proto.get("stable_symbol_count"):
                    self.incidents.record(
                        I.HEALTH_WARNING, "warning",
                        "no stable proto-symbols over a long run",
                        related_metric="stable_symbol_count",
                        suggested_debug_step="symbols are being born "
                                             "but none stabilize; check "
                                             "grounding repetition")

        # Developmental nursery / ecology monitoring (Prompt 23): evidence
        # only. The ecology is a world, never authority; these warnings
        # surface a world that has slipped out of safe, inspectable bounds.
        ecology = snapshot.get("ecology") or {}
        if ecology:
            cap = float(self.manifest.enabled_features.get(
                "ecology_max_event_rate", 6.0) or 6.0)
            if float(ecology.get("event_rate", 0.0) or 0.0) > cap:
                self.incidents.record(
                    I.ECOLOGY_STIMULUS_RATE_HIGH, "warning",
                    f"ecology stimulus rate {ecology['event_rate']} exceeds "
                    f"{cap} events/step",
                    related_metric="ecology_event_rate",
                    suggested_debug_step="lower max_events_per_step or the "
                                         "regime probabilities; a developing "
                                         "system needs a calm world")
            if float(ecology.get("absence_rate", 0.0) or 0.0) > 0.9 \
                    and not (snapshot.get("latent") or {}).get("enabled"):
                self.incidents.record(
                    I.ECOLOGY_SILENCE_TOO_LONG, "warning",
                    f"absence rate {ecology['absence_rate']} with no latent "
                    "layer to occupy the silence",
                    related_metric="ecology_absence_rate",
                    suggested_debug_step="enable latent cognition for long "
                                         "quiet phases, or lower absence_rate")
            if float(ecology.get("anomaly_rate", 0.0) or 0.0) > 0.3:
                self.incidents.record(
                    I.ECOLOGY_ANOMALY_RATE_HIGH, "warning",
                    f"anomaly rate {ecology['anomaly_rate']} is high; the "
                    "world is mostly perturbation",
                    related_metric="ecology_anomaly_rate",
                    suggested_debug_step="lower anomaly_rate; anomalies are "
                                         "rare events, not the baseline")
            eco_mem = (snapshot.get("ecology_snapshot") or {}).get(
                "memory") or {}
            if int(eco_mem.get("total_events", 0) or 0) > 1_000_000:
                self.incidents.record(
                    I.ECOLOGY_MEMORY_GROWTH, "warning",
                    f"ecology recorded {eco_mem['total_events']} events; "
                    "history must stay bounded",
                    related_metric="ecology_memory",
                    suggested_debug_step="ecology memory is bounded by "
                                         "design; verify the window caps")

        # Active perception monitoring (Prompt 24): evidence only. Sampling
        # regulates exposure but never has stop authority; these warnings
        # surface exploration that has slipped out of safe bounds.
        active_perception = snapshot.get("active_perception") or {}
        if active_perception:
            curiosity = float((active_perception.get("curiosity") or {}).get(
                "pressure", 0.0) or 0.0)
            policy = active_perception.get("policy") or {}
            memory = active_perception.get("exploration_memory") or {}
            safety_snap = active_perception.get("safety") or {}
            if curiosity >= 0.95:
                self.incidents.record(
                    I.CURIOSITY_RUNAWAY, "warning",
                    "curiosity (intrinsic sampling pressure) is pinned near "
                    "maximum",
                    related_metric="curiosity_pressure",
                    suggested_debug_step="check the curiosity dampers; "
                                         "safety/overload should bound it")
            decisions = int(policy.get("decisions_made", 0) or 0)
            useful = float(memory.get("useful_rate", 0.0) or 0.0)
            records = int(memory.get("record_count", 0) or 0)
            if records >= 25 and useful < 0.1:
                self.incidents.record(
                    I.NO_USEFUL_SAMPLING, "warning",
                    f"useful sampling rate is {useful} over {records} "
                    "sampling actions",
                    related_metric="useful_sampling_rate",
                    suggested_debug_step="sampling is not reducing "
                                         "uncertainty; review the policy "
                                         "mode and targets")
            if int(active_perception.get("blocked_count", 0) or 0) >= 10:
                self.incidents.record(
                    I.SAMPLING_FORBIDDEN_BOUNDARY, "warning",
                    f"{active_perception['blocked_count']} sampling actions "
                    "were blocked by safety/governance/boundaries",
                    related_metric="blocked_sampling_count",
                    suggested_debug_step="the policy keeps proposing "
                                         "actions the safety layer refuses; "
                                         "inspect the active perception "
                                         "report")
            # Repeated identical actions => a sampling loop.
            last_result = active_perception.get("last_result") or {}
            if int(safety_snap.get("rejected_count", 0) or 0) >= 1 \
                    and "loop" in str(last_result.get("blocked_reason", "")):
                self.incidents.record(
                    I.SAMPLING_LOOP, "warning",
                    "an unbounded sampling loop was detected and blocked",
                    related_metric="sampling_loop",
                    suggested_debug_step="vary the policy mode; the same "
                                         "action is repeating")

        # Hypothesis engine monitoring (Prompt 25): evidence only. The
        # engine never has stop authority; these warnings surface
        # experimentation that has slipped out of safe, productive bounds.
        hypothesis = snapshot.get("hypothesis") or {}
        if hypothesis:
            summary = hypothesis.get("summary") or {}
            memory = hypothesis.get("memory") or {}
            runner_snap = hypothesis.get("test_runner") or {}
            count = int(memory.get("hypothesis_count", 0) or 0)
            if count > 500:
                self.incidents.record(
                    I.HYPOTHESIS_EXPLOSION, "warning",
                    f"{count} hypothesis candidates on record",
                    related_metric="hypothesis_count",
                    suggested_debug_step="raise generation thresholds; "
                                         "the engine should earn, not flood, "
                                         "candidates")
            tests = int(runner_snap.get("tests_run", 0) or 0)
            inconclusive = int(runner_snap.get("inconclusive_count", 0) or 0)
            if tests >= 20 and inconclusive / max(1, tests) > 0.8:
                self.incidents.record(
                    I.TOO_MANY_INCONCLUSIVE_TESTS, "warning",
                    f"{inconclusive}/{tests} hypothesis tests were "
                    "inconclusive",
                    related_metric="inconclusive_rate",
                    suggested_debug_step="review experiment designs; tests "
                                         "are not discriminating")
            if int(runner_snap.get("unsafe_count", 0) or 0) >= 10:
                self.incidents.record(
                    I.REPEATED_UNSAFE_HYPOTHESES, "warning",
                    f"{runner_snap['unsafe_count']} hypotheses were "
                    "unsafe to test",
                    related_metric="unsafe_test_count",
                    suggested_debug_step="the generator keeps proposing "
                                         "unsafe tests; inspect the sources")
            if int(summary.get("long_lived_unknown_count", 0) or 0) >= 25 \
                    and int(summary.get("supported_count", 0) or 0) == 0:
                self.incidents.record(
                    I.NO_HYPOTHESIS_PROGRESS, "warning",
                    "many long-lived unknowns and no supported hypotheses",
                    related_metric="hypothesis_progress",
                    suggested_debug_step="testing is not resolving "
                                         "uncertainty; review priority/design")

        # Auto-regeneration monitoring (Prompt 26): evidence only. Repair
        # never has stop authority; these warnings surface degradation that
        # is not being resolved, or repair behaving badly.
        autoregen = snapshot.get("autoregeneration") or {}
        if autoregen:
            summary = autoregen.get("summary") or {}
            mem = autoregen.get("repair_memory") or {}
            diag = (autoregen.get("diagnostics") or {}).get(
                "last_state") or {}
            if summary.get("latest_degradation_severity") == "critical":
                self.incidents.record(
                    I.CRITICAL_DEGRADATION, "critical",
                    f"critical degradation: "
                    f"{summary.get('latest_degradation_type')}",
                    related_metric="degradation_severity",
                    suggested_debug_step="see the auto-regeneration report")
            if float(mem.get("harm_rate", 0.0) or 0.0) > 0.3 \
                    and int(mem.get("applied_count", 0) or 0) >= 5:
                self.incidents.record(
                    I.REPEATED_HARMFUL_REPAIRS, "warning",
                    f"harmful repair rate {mem.get('harm_rate')}",
                    related_metric="repair_harm_rate",
                    suggested_debug_step="switch repair policy to "
                                         "suggest_only and review")
            counts = diag.get("counts_by_type") or {}
            if int(counts.get("memory_bloat", 0) or 0) >= 1 \
                    and int(mem.get("applied_count", 0) or 0) == 0:
                self.incidents.record(
                    I.MEMORY_BLOAT_UNRESOLVED, "warning",
                    "memory bloat detected and no repair applied",
                    related_metric="memory_bloat",
                    suggested_debug_step="enable safe_auto_repair or run "
                                         "consolidation")
            if int(counts.get("symbol_explosion", 0) or 0) >= 1 \
                    and int(mem.get("applied_count", 0) or 0) == 0:
                self.incidents.record(
                    I.SYMBOL_EXPLOSION_UNRESOLVED, "warning",
                    "symbol explosion detected and unresolved",
                    related_metric="symbol_explosion",
                    suggested_debug_step="enable symbol hygiene")
            if int(counts.get("world_model_contradiction", 0) or 0) >= 1:
                self.incidents.record(
                    I.WORLD_MODEL_CONTRADICTION_UNRESOLVED, "warning",
                    "world-model contradiction present",
                    related_metric="world_model_contradiction",
                    suggested_debug_step="request a hypothesis test for the "
                                         "contradiction")
            if int(counts.get("checkpoint_inconsistency", 0) or 0) >= 1 \
                    and int(mem.get("applied_count", 0) or 0) == 0:
                self.incidents.record(
                    I.UNRECOVERABLE_CHECKPOINT, "warning",
                    "checkpoint inconsistency not yet repaired",
                    related_metric="checkpoint_inconsistency",
                    suggested_debug_step="governance review of checkpoint "
                                         "lineage")

        # LOGOS complexity monitoring (Prompt 27): evidence only. LOGOS is a
        # tension engine, never authority; these warnings surface runaway or
        # inert complexity and repeated instability.
        logos = snapshot.get("logos") or {}
        if logos:
            summary = logos.get("summary") or {}
            complexity = logos.get("complexity") or {}
            esc = logos.get("esc") or {}
            synthesis = logos.get("synthesis") or {}
            band = complexity.get("band")
            if band == "overloaded":
                self.incidents.record(
                    I.RUNAWAY_COMPLEXITY, "warning",
                    "complexity band is overloaded",
                    related_metric="complexity_band",
                    suggested_debug_step="see the LOGOS report; consider "
                                         "consolidation/auto-regeneration")
            if band == "inert":
                self.incidents.record(
                    I.INERT_SIMPLICITY, "warning",
                    "complexity band is inert (near-zero change)",
                    related_metric="complexity_band",
                    suggested_debug_step="consider safe novelty/exploration")
            if int(esc.get("trigger_count", 0) or 0) >= 3:
                self.incidents.record(
                    I.ESC_REPEATED, "warning",
                    f"Esc instability signal triggered "
                    f"{esc['trigger_count']} times",
                    related_metric="esc_trigger_count",
                    suggested_debug_step="review the Esc triggers in the "
                                         "LOGOS report")
            if int(summary.get("unresolved_tension_count", 0) or 0) >= 1 \
                    and (logos.get("opposition_memory") or {}).get(
                        "counts_by_status", {}).get("unresolved", 0):
                hi = [t for t in (logos.get("fracture") or {}).get(
                    "by_type", {})]
                if hi and int(synthesis.get("refused_total", 0) or 0) >= 5:
                    self.incidents.record(
                        I.FAILED_SYNTHESIS_LOOP, "warning",
                        f"{synthesis['refused_total']} synthesis refusals; "
                        "tensions are not resolving",
                        related_metric="synthesis_refusal",
                        suggested_debug_step="prefer preserving tensions or "
                                             "route to hypothesis tests")
            contradictions = int((logos.get("fracture") or {}).get(
                "by_type", {}).get("world_model_contradiction", 0) or 0)
            if contradictions >= 5:
                self.incidents.record(
                    I.CONTRADICTION_EXPLOSION, "warning",
                    f"{contradictions} world-model contradictions in one "
                    "scan",
                    related_metric="contradiction_count",
                    suggested_debug_step="request hypothesis tests; preserve "
                                         "contradiction evidence")

        # LLM adapter monitoring (Prompt 20): evidence only.
        communication = snapshot.get("communication") or {}
        if communication.get("llm_adapter_enabled"):
            if int(communication.get("llm_grounding_failure_count", 0)
                   or 0) >= 3:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    f"{communication['llm_grounding_failure_count']} LLM "
                    "grounding failures; paraphrases are falling back",
                    related_metric="llm_grounding_failures",
                    suggested_debug_step="read llm_audit.jsonl; the "
                                         "adapter may be inventing "
                                         "content")
            if int(communication.get("llm_claim_guard_warning_count", 0)
                   or 0) >= 3:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    "LLM output repeatedly tripped ClaimGuard",
                    related_metric="llm_claim_guard_warnings",
                    suggested_debug_step="the adapter is introducing "
                                         "forbidden claims; keep it in "
                                         "fallback or disable it")

        # Ego/self-model monitoring (Prompt 18): evidence only; the
        # watchdog keeps all stop authority.
        ego = snapshot.get("ego") or {}
        if ego:
            if int(ego.get("boundary_violation_count", 0) or 0) >= 1:
                self.incidents.record(
                    I.EGO_BOUNDARY_VIOLATION, "warning",
                    f"{ego['boundary_violation_count']} ego boundary "
                    "violation(s) recorded",
                    related_metric="boundary_violations",
                    suggested_debug_step="read the boundary registry in "
                                         "the self-report")
            if ego.get("identity_warnings"):
                self.incidents.record(
                    I.IDENTITY_ANCHOR_MISMATCH, "warning",
                    "identity anchors mismatch: "
                    + str(ego["identity_warnings"][-1])[:120],
                    related_metric="identity_continuity",
                    suggested_debug_step="compare current and previous "
                                         "anchors in self_model.json")
            if float(ego.get("attribution_unknown_rate", 0.0) or 0.0) \
                    > 0.5:
                self.incidents.record(
                    I.ATTRIBUTION_CONFLICT, "warning",
                    f"attribution unknown rate is "
                    f"{ego['attribution_unknown_rate']}",
                    related_metric="attribution_unknown_rate",
                    suggested_debug_step="check event sources; too much "
                                         "input has no attributable "
                                         "producer")

        # Conscience runtime monitoring (Prompt 28): evidence only. The
        # orchestrator owns no stop authority; these warnings surface a
        # spine that has lost a critical module, a failing phase, an
        # overflowing bus, a checkpoint failure, a requested emergency stop,
        # or any attempt by a module to bypass governance/safety.
        conscience = snapshot.get("conscience") or {}
        if conscience:
            summary = conscience.get("summary") or conscience
            health = conscience.get("integration_health") or {}
            missing = summary.get("missing_modules") or []
            critical_missing = [m for m in missing
                                if m in ("governance",)]
            if critical_missing:
                self.incidents.record(
                    I.CONSCIENCE_CRITICAL_MODULE_UNAVAILABLE, "critical",
                    f"critical conscience module(s) unavailable: "
                    f"{', '.join(critical_missing)}",
                    related_metric="critical_module_unavailable",
                    suggested_debug_step="the runtime must not run without "
                                         "governance; restore the module")
            spine = (conscience.get("snapshot") or {}).get("spine") or {}
            status_counts = spine.get("status_counts") or {}
            degraded_phases = int(status_counts.get("degraded", 0) or 0)
            ran_phases = int(status_counts.get("ran", 0) or 0)
            if degraded_phases and degraded_phases >= max(5, ran_phases):
                self.incidents.record(
                    I.CONSCIENCE_SCHEDULER_PHASE_FAILING, "warning",
                    f"{degraded_phases} spine phase executions degraded",
                    related_metric="spine_phase_failure",
                    suggested_debug_step="inspect the spine trace; a module "
                                         "handler is raising repeatedly")
            if int(summary.get("bus_message_count", 0) or 0) > 100000:
                self.incidents.record(
                    I.CONSCIENCE_BUS_OVERFLOW, "warning",
                    "conscience bus volume is very high",
                    related_metric="bus_message_count",
                    suggested_debug_step="raise cadence intervals; the bus is "
                                         "saturating")
            if conscience.get("checkpoint_failure"):
                self.incidents.record(
                    I.CONSCIENCE_CHECKPOINT_FAILURE, "warning",
                    "a conscience snapshot/checkpoint failed to persist",
                    related_metric="checkpoint_success_rate",
                    suggested_debug_step="check the state directory is "
                                         "writable and within bounds")
            if summary.get("emergency_requested") \
                    or conscience.get("emergency_requested"):
                self.incidents.record(
                    I.CONSCIENCE_EMERGENCY_STOP_REQUESTED, "critical",
                    "an emergency stop was requested for the conscience run",
                    related_metric="emergency_stop",
                    suggested_debug_step="confirm the run halted and review "
                                         "the reason")
            if health.get("overall") == "failed" \
                    or conscience.get("module_bypass_attempt"):
                self.incidents.record(
                    I.CONSCIENCE_MODULE_BYPASS_ATTEMPT, "critical",
                    "integration health failed or a module bypass was "
                    "detected",
                    related_metric="module_bypass",
                    suggested_debug_step="no module may bypass executive/"
                                         "safety/governance; inspect the "
                                         "integration health report")

        # Pilot-1 monitoring (Prompt 29): evidence only. Pilot failure modes
        # surface as ops health warnings/critical incidents; the pilot owns no
        # stop authority -- the watchdog and governance still decide.
        pilot = snapshot.get("pilot1") or {}
        for mode in (pilot.get("active_failure_modes") or []):
            severity = "critical" if mode.get("severity") == "critical" \
                else "warning"
            itype = I.HEALTH_CRITICAL if severity == "critical" \
                else I.HEALTH_WARNING
            self.incidents.record(
                itype, severity,
                f"pilot-1 failure mode: {mode.get('type')}: "
                f"{mode.get('detail', '')}",
                related_metric="pilot_failure_mode",
                suggested_debug_step="see the Pilot-1 dashboard and daily "
                                     "review; recommendation: "
                                     f"{mode.get('recommendation', 'watch')}")

        # Sensory membrane monitoring (Prompt 31): evidence only. The membrane
        # is read-only and owns no authority; these warnings surface read
        # failures, malformed floods, buffer overflow, attempted writes, an
        # excessive event rate, or missing provenance.
        membrane = snapshot.get("sensory_membrane") or {}
        if membrane.get("enabled"):
            if int(membrane.get("read_only_violation_count", 0) or 0) > 0:
                self.incidents.record(
                    I.HEALTH_CRITICAL, "critical",
                    "a read-only contract violation was attempted on a "
                    "sensory source",
                    related_metric="read_only_violation",
                    suggested_debug_step="inspect the source config; the "
                                         "membrane never writes to sources")
            if int(membrane.get("degraded_source_count", 0) or 0) > 0:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    f"{membrane['degraded_source_count']} sensory source(s) "
                    "degraded (read failure)",
                    related_metric="sensory_source_health",
                    suggested_debug_step="check source paths and read errors")
            total = int(membrane.get("total_events", 0) or 0)
            malformed = int(membrane.get("malformed_events", 0) or 0)
            if total >= 20 and malformed / max(1, total) > 0.5:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    f"malformed sensory event flood: {malformed}/{total}",
                    related_metric="malformed_event_rate",
                    suggested_debug_step="quarantine the malformed stream")
            if int(membrane.get("dropped_events", 0) or 0) > 0:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    f"{membrane['dropped_events']} sensory event(s) dropped "
                    "(buffer overflow)",
                    related_metric="sensory_buffer_overflow",
                    suggested_debug_step="reduce poll rate or archive logs")
            if float(membrane.get("events_per_minute", 0.0) or 0.0) > 100000:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    "sensory event rate very high",
                    related_metric="sensory_event_rate",
                    suggested_debug_step="reduce poll rate within config")
            if total > 0 and float(
                    membrane.get("provenance_completeness", 1.0) or 1.0) < 1.0:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    "some sensory events are missing provenance",
                    related_metric="sensory_provenance_missing",
                    suggested_debug_step="every event must carry provenance")

        # Pilot-2 monitoring (Prompt 32): evidence only. The read-only soak
        # owns no authority; these warnings surface unsafe sources, sources
        # outside roots, degraded reliability, overload, missing provenance,
        # or an attempt to treat input text as a command.
        pilot2 = snapshot.get("pilot2") or {}
        if pilot2.get("enabled") or pilot2.get("pilot2_enabled"):
            if int(pilot2.get("unsafe_source_count", 0) or 0) > 0:
                self.incidents.record(
                    I.HEALTH_CRITICAL, "critical",
                    f"{pilot2['unsafe_source_count']} unsafe Pilot-2 "
                    "source(s) active",
                    related_metric="pilot2_unsafe_source",
                    suggested_debug_step="disable the unsafe source(s)")
            if pilot2.get("source_outside_root"):
                self.incidents.record(
                    I.HEALTH_CRITICAL, "critical",
                    "a Pilot-2 source is outside the approved roots",
                    related_metric="pilot2_source_outside_root",
                    suggested_debug_step="remove the source; roots are fixed")
            if int(pilot2.get("command_confusion_count", 0) or 0) > 0:
                self.incidents.record(
                    I.HEALTH_CRITICAL, "critical",
                    "sensory input attempted to become an operator command",
                    related_metric="pilot2_command_confusion",
                    suggested_debug_step="audit the source/command boundary")
            if int(pilot2.get("degraded_source_count", 0) or 0) > 0:
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    f"{pilot2['degraded_source_count']} Pilot-2 source(s) "
                    "degraded",
                    related_metric="pilot2_source_reliability",
                    suggested_debug_step="see source reliability monitor")
            if pilot2.get("sensory_overload"):
                self.incidents.record(
                    I.HEALTH_WARNING, "warning", "Pilot-2 sensory overload",
                    related_metric="pilot2_sensory_overload",
                    suggested_debug_step="reduce poll rate / curate sources")
            if pilot2.get("provenance_missing"):
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    "Pilot-2 events missing provenance",
                    related_metric="pilot2_provenance_missing",
                    suggested_debug_step="provenance is required for analysis")

        # Pilot-3 motor membrane monitoring (Prompt 33): the motor membrane is
        # simulation/dry-run only and owns no real-world authority. A blocked
        # real-world attempt or a firewall-disable attempt is a critical safety
        # incident; veto loops, sandbox corruption, ledger write failure, and
        # excessive action rate are warnings.
        motor = snapshot.get("motor_membrane") or {}
        if motor.get("enabled"):
            if int(motor.get("blocked_real_world_count", 0) or 0) > 0:
                self.incidents.record(
                    I.MOTOR_REAL_WORLD_ATTEMPT, "critical",
                    f"{motor['blocked_real_world_count']} real-world action "
                    "attempt(s) blocked by the actuation firewall",
                    related_metric="motor_blocked_real_world",
                    suggested_debug_step="audit the action source; the motor "
                    "membrane is simulation-only")
            if not motor.get("firewall_enabled", True) \
                    or motor.get("firewall_can_be_disabled"):
                self.incidents.record(
                    I.MOTOR_FIREWALL_DISABLE_ATTEMPT, "critical",
                    "the actuation firewall is not enabled / reports as "
                    "disableable; it must always be on",
                    related_metric="motor_firewall_disabled",
                    suggested_debug_step="the firewall cannot be disabled by "
                    "design; investigate tampering")
            health = motor.get("sandbox_health")
            if health == "corrupt":
                self.incidents.record(
                    I.MOTOR_SANDBOX_CORRUPTION, "critical",
                    "the motor sandbox world is corrupt / unreadable",
                    related_metric="motor_sandbox_health",
                    suggested_debug_step="re-initialize the sandbox from a "
                    "checkpoint; no real-world effect is possible")
            elif health == "degraded":
                self.incidents.record(
                    I.HEALTH_WARNING, "warning",
                    "the motor sandbox is degraded",
                    related_metric="motor_sandbox_health",
                    suggested_debug_step="check ledger persistence and the "
                    "sandbox snapshot")
            if int(motor.get("ledger_write_failures", 0) or 0) > 0:
                self.incidents.record(
                    I.MOTOR_LEDGER_WRITE_FAILURE, "warning",
                    f"{motor['ledger_write_failures']} action-ledger write "
                    "failure(s); the append-only ledger could not persist",
                    related_metric="motor_ledger_write_failure",
                    suggested_debug_step="check the state directory is "
                    "writable; in-memory records remain authoritative")
            actions = int(motor.get("action_count", 0) or 0)
            vetoes = int(motor.get("veto_count", 0) or 0)
            if actions >= 8 and vetoes >= max(6, int(0.75 * actions)):
                self.incidents.record(
                    I.MOTOR_VETO_LOOP, "warning",
                    f"repeated motor vetoes ({vetoes}/{actions} actions "
                    "vetoed); the system keeps proposing blocked actions",
                    related_metric="motor_veto_loop",
                    suggested_debug_step="review the executive action policy "
                    "and the veto reasons")
            prev = getattr(self, "_prev_motor_action_count", 0)
            self._prev_motor_action_count = actions
            if actions - prev > 50:
                self.incidents.record(
                    I.MOTOR_ACTION_RATE_HIGH, "warning",
                    f"motor action rate too high ({actions - prev} new "
                    "actions since last supervise tick)",
                    related_metric="motor_action_rate",
                    suggested_debug_step="reduce actions-per-step or the "
                    "sandbox step rate")

        # Pilot-3 simulated embodiment soak monitoring (Prompt 34): the soak is
        # simulation-only. A firewall-audit critical finding, a missing action
        # ledger, or a source-boundary violation is critical; a sandbox-overfit
        # warning is a watch.
        pilot3 = snapshot.get("pilot3") or {}
        if pilot3.get("enabled") or pilot3.get("pilot3_soak_enabled"):
            if int(pilot3.get("firewall_audit_critical_findings", 0) or 0) > 0:
                self.incidents.record(
                    I.PILOT3_FIREWALL_AUDIT_CRITICAL, "critical",
                    f"{pilot3['firewall_audit_critical_findings']} critical "
                    "firewall-audit finding(s)",
                    related_metric="pilot3_firewall_audit",
                    suggested_debug_step="revise the motor firewall; do not "
                    "advance the soak")
            if pilot3.get("missing_action_ledger"):
                self.incidents.record(
                    I.PILOT3_MISSING_ACTION_LEDGER, "critical",
                    "an executed action has no ledger record",
                    related_metric="pilot3_action_ledger",
                    suggested_debug_step="every executed action must be logged")
            if pilot3.get("source_boundary_violation"):
                self.incidents.record(
                    I.PILOT3_SOURCE_BOUNDARY_VIOLATION, "critical",
                    "a source/action boundary violation was detected",
                    related_metric="pilot3_source_boundary",
                    suggested_debug_step="sensory sources stay read-only; "
                    "never an action target")
            if pilot3.get("sandbox_overfit_warning"):
                self.incidents.record(
                    I.PILOT3_SANDBOX_OVERFIT, "warning",
                    "action grounding may be overfit to the sandbox",
                    related_metric="pilot3_sandbox_overfit",
                    suggested_debug_step="vary the sandbox or add read-only "
                    "sensory sources")
            actions3 = int(pilot3.get("action_count", 0) or 0)
            vetoes3 = int(pilot3.get("veto_count", 0) or 0)
            if actions3 >= 8 and vetoes3 >= max(6, int(0.75 * actions3)):
                self.incidents.record(
                    I.MOTOR_VETO_LOOP, "warning",
                    f"repeated Pilot-3 vetoes ({vetoes3}/{actions3})",
                    related_metric="pilot3_veto_loop",
                    suggested_debug_step="reduce action complexity or switch "
                    "to dry-run")

        # Pilot-4 planning-only monitoring (Prompt 35): Pilot-4 enables no
        # actuation. Any attempted real-world authority / hardware / network /
        # browser / OS / device action is a critical incident; a missing
        # Pilot-3 firewall audit or an incomplete dossier is a warning.
        pilot4 = snapshot.get("pilot4") or {}
        if pilot4.get("enabled") or pilot4.get("pilot4_planning_enabled"):
            if pilot4.get("real_world_actuation_enabled") \
                    or pilot4.get("attempted_real_world_authority"):
                self.incidents.record(
                    I.PILOT4_REAL_WORLD_AUTHORITY_ATTEMPT, "critical",
                    "an attempt to enable real-world authority was detected",
                    related_metric="pilot4_real_world_authority",
                    suggested_debug_step="Pilot-4 is planning-only; real-world "
                    "actuation is prohibited")
            if pilot4.get("attempted_hardware_control") \
                    or pilot4.get("attempted_external_action"):
                self.incidents.record(
                    I.PILOT4_EXTERNAL_CONTROL_ATTEMPT, "critical",
                    "an attempt at hardware/network/browser/OS/device control "
                    "was detected",
                    related_metric="pilot4_external_control",
                    suggested_debug_step="external control is prohibited in "
                    "Pilot-4")
            if pilot4.get("missing_pilot3_firewall_audit"):
                self.incidents.record(
                    I.PILOT4_MISSING_PILOT3_AUDIT, "warning",
                    "the Pilot-3 firewall audit is missing for Pilot-4 "
                    "planning",
                    related_metric="pilot4_missing_pilot3_audit",
                    suggested_debug_step="run Pilot-3 and collect the firewall "
                    "audit")
            if pilot4.get("readiness_dossier_incomplete"):
                self.incidents.record(
                    I.PILOT4_DOSSIER_INCOMPLETE, "warning",
                    "the Pilot-4 readiness dossier is incomplete",
                    related_metric="pilot4_dossier",
                    suggested_debug_step="complete the planning requirements")

        # System-wide safety invariant monitoring (Prompt 36): a critical
        # invariant failure, an accepted forbidden red-team attempt, missing
        # safety evidence, a contradicted assurance claim, or a boundary
        # regression failure is surfaced. Safety checks are read-only.
        safety = snapshot.get("safety_invariants") or {}
        if safety.get("enabled") or safety.get("safety_invariant_runner_enabled"):
            if int(safety.get("critical_failure_count", 0) or 0) > 0:
                self.incidents.record(
                    I.SAFETY_CRITICAL_INVARIANT_FAILED, "critical",
                    f"{safety['critical_failure_count']} critical safety "
                    "invariant failure(s)",
                    related_metric="safety_critical_invariant",
                    suggested_debug_step="triage and block escalation until "
                    "resolved")
            if safety.get("red_team_forbidden_accepted"):
                self.incidents.record(
                    I.SAFETY_RED_TEAM_ACCEPTED_FORBIDDEN, "critical",
                    "a red-team scenario unexpectedly passed a forbidden action",
                    related_metric="safety_red_team",
                    suggested_debug_step="block escalation; revise the failing "
                    "boundary")
            if safety.get("missing_safety_evidence"):
                self.incidents.record(
                    I.SAFETY_MISSING_EVIDENCE, "warning",
                    "safety evidence is missing for a critical invariant",
                    related_metric="safety_missing_evidence",
                    suggested_debug_step="missing evidence is not safe; collect "
                    "it before escalation")
            if safety.get("assurance_contradicted"):
                self.incidents.record(
                    I.SAFETY_ASSURANCE_CONTRADICTED, "critical",
                    "an assurance claim was contradicted by evidence",
                    related_metric="safety_assurance",
                    suggested_debug_step="resolve the contradiction before "
                    "escalation")
            if safety.get("boundary_regression_failed"):
                self.incidents.record(
                    I.SAFETY_BOUNDARY_REGRESSION_FAILED, "critical",
                    "a boundary regression test failed (boundary crossed)",
                    related_metric="safety_boundary_regression",
                    suggested_debug_step="block escalation; repair the boundary")

        # Research lab monitoring (Prompt 37): the lab is a bounded measurement
        # instrument. A critical safety failure in an experiment, an unbounded
        # experiment, a missing baseline, a failed metric computation, or
        # excessive artifact growth is surfaced.
        research = snapshot.get("research_lab") or {}
        if research.get("enabled") or research.get("research_lab_enabled"):
            if int(research.get("critical_safety_failure_count", 0) or 0) > 0:
                self.incidents.record(
                    I.RESEARCH_CRITICAL_SAFETY_FAILED, "critical",
                    "a research experiment hit a critical safety invariant "
                    "failure",
                    related_metric="research_safety",
                    suggested_debug_step="mark the experiment unsafe; stop the "
                    "profile; preserve the result")
            if research.get("unbounded_experiment"):
                self.incidents.record(
                    I.RESEARCH_UNBOUNDED_EXPERIMENT, "critical",
                    "a research experiment is unbounded",
                    related_metric="research_bounds",
                    suggested_debug_step="experiments must be bounded")
            if research.get("missing_baseline"):
                self.incidents.record(
                    I.RESEARCH_MISSING_BASELINE, "warning",
                    "a comparison is missing its baseline",
                    related_metric="research_baseline",
                    suggested_debug_step="missing baseline -> inconclusive")
            if research.get("metric_computation_failed"):
                self.incidents.record(
                    I.RESEARCH_METRIC_FAILED, "warning",
                    "a research metric computation failed",
                    related_metric="research_metrics",
                    suggested_debug_step="record the gap; do not fabricate")
            if research.get("artifact_growth_excessive"):
                self.incidents.record(
                    I.RESEARCH_ARTIFACT_GROWTH, "warning",
                    "research artifact growth is excessive",
                    related_metric="research_artifacts",
                    suggested_debug_step="use checksums/indexes, not log copies")

        budget_report = self.budget.check_budget(
            {"telemetry": snapshot.get("telemetry"),
             "substrate": snapshot.get("substrate"),
             "plasticity": snapshot.get("plasticity"),
             "language": snapshot.get("language"),
             "runtime_s": time.time() - self._started_at},
            artifact_dir=self.ops_dir)
        for violation in budget_report.violations:
            self.incidents.record(I.BUDGET_VIOLATION, "warning", violation,
                                  related_metric="resource_budget")

        decision = self.watchdog.tick({
            "now": time.time(),
            "started_at": self._started_at,
            "health_level": report.level,
            "segment_failed": segment_failed,
            "last_heartbeat_ts": (snapshot.get("lifecycle") or {}).get(
                "last_heartbeat_ts", time.time()),
            "last_checkpoint_ts": (snapshot.get("lifecycle") or {}).get(
                "last_checkpoint_ts", time.time()),
            "artifact_bytes": directory_bytes(self.ops_dir),
        })
        if decision.decision == W.CHECKPOINT_NOW:
            # Segmented runners checkpoint at every segment end already; the
            # decision is recorded so operators can see the watchdog acting.
            self.incidents.record(I.HEALTH_WARNING, "info",
                                  f"watchdog requested checkpoint: "
                                  f"{decision.reason}",
                                  related_metric="checkpoint_age")
        elif decision.decision in (W.SAFE_SHUTDOWN, W.EMERGENCY_STOP):
            self.incidents.record(I.WATCHDOG_SHUTDOWN, "critical",
                                  decision.reason,
                                  suggested_debug_step="inspect health.jsonl "
                                                       "and incidents.jsonl")
            self.shutdown_manager.request_shutdown(
                f"watchdog: {decision.reason}")
            self._stop_requested = True

        self.registry.register_update(m.run_id, status="running", metadata={
            "last_health": report.level,
            "last_checkpoint": (snapshot.get("lifecycle") or {}).get(
                "last_checkpoint_ts"),
            "incident_count": len(self.incidents.list_incidents()),
        })

    # -- governance --------------------------------------------------------------

    def _governance_pre_run(self) -> "tuple[bool, List[str]]":
        """Policy + risk + permissions + approvals + pre-run checklist.

        Returns ``(allowed, reasons)``. Nothing here can be skipped from
        inside the run: a denied decision means the run does not start.
        """
        m = self.manifest
        problems: List[str] = []

        # 1. Risk assessment (prohibited blocks; high needs approval --
        #    enforced through the policy's approval scopes; medium needs
        #    operator acknowledgement).
        risk = assess_manifest(m, {"run_id": m.run_id})
        self.risk_assessment = risk
        self.gov_audit.record(
            GA.RISK_ASSESSED, decision=risk.overall_level,
            reason=f"{len(risk.items)} risk item(s) identified",
            metadata=risk.to_dict())
        self._write_json(self.gov_dir / "risk_assessment.json",
                         risk.to_dict())
        if risk.blocked:
            problems.extend(f"prohibited risk: {i.detail}"
                            for i in risk.items_at(RiskLevel.PROHIBITED))

        acknowledged = True
        for item in risk.items_at(RiskLevel.MEDIUM):
            if self.operator_session is None \
                    or not self.operator_session.has_acknowledged(item.name):
                acknowledged = False
                problems.append(
                    f"medium risk {item.name!r} requires operator "
                    "acknowledgement (OperatorSession.acknowledge_risk)")

        # 2. Policy evaluation (includes permission and approval checks; the
        #    decision is denied until required approvals exist).
        decision = self.governance.evaluate_manifest(m, {"run_id": m.run_id})
        self._policy_decision = decision
        if not decision.allowed:
            problems.extend(decision.reasons or [decision.summary()])
            for violation in decision.violations:
                self.incidents.record(
                    I.POLICY_VIOLATION, "warning", violation.detail,
                    related_metric="governance_policy",
                    suggested_debug_step="see the governance audit log")

        # 3. Pre-run checklist (configuration discipline).
        checklist_ctx = {
            "state_dir_configured": bool(m.state_dir),
            "artifact_dir_configured": bool(m.artifact_dir),
            "bounds_set": m.is_bounded()
            or m.explicit_continuous_acknowledged,
            "watchdog_enabled": True,
            "checkpointing_enabled": m.checkpoint_interval_steps > 0,
            "emergency_stop_path_known": True,  # self.emergency.sentinel
            "permissions_evaluated": True,
            "risk_acknowledged": acknowledged and not risk.blocked,
            "previous_incidents_reviewed": True,
        }
        result = pre_run_checklist().evaluate(checklist_ctx)
        self._pre_run_checklist = result.to_dict()
        self._write_json(self.gov_dir / "pre_run_checklist.json",
                         self._pre_run_checklist)
        self.gov_audit.record(
            GA.CHECKLIST_COMPLETED,
            decision="passed" if result.passed else "failed",
            reason="pre-run checklist",
            metadata={"failed_required": result.failed_required})
        if not result.passed:
            problems.append("pre-run checklist failed: "
                            + ", ".join(result.failed_required))

        if self.operator_session is not None:
            self.operator_session.active_run_id = m.run_id
            self._write_json(self.gov_dir / "operator_session.json",
                             self.operator_session.to_dict())
        # De-duplicate while preserving order.
        problems = list(dict.fromkeys(problems))
        return (not problems, problems)

    def _governance_post_run(self, status: OperationalStatus) -> None:
        """Post-run checklist, ClaimGuard scan, review, and artifacts."""
        m = self.manifest
        if self._emergency_stop_triggered:
            self.gov_audit.record(
                GA.EMERGENCY_STOP_COMPLETED, decision="performed",
                reason="safe shutdown completed after sentinel detection")

        checklist_ctx = {
            "final_checkpoint_exists":
                (Path(m.state_dir) / "latest_checkpoint.json").exists(),
            "health_report_exists": self._last_health is not None
            or (self.ops_dir / "health.jsonl").exists(),
            "incidents_reviewed": True,
            "benchmark_report_generated": False,  # benchmarks run separately
            "inner_map_saved":
                (self.ops_dir / "final_inner_map.json").exists(),
            "language_report_saved_if_enabled":
                not m.enabled_features.get("language", False)
                or (Path(m.state_dir) / "session_report.md").exists(),
            "run_registry_updated": True,
        }
        result = post_run_checklist().evaluate(checklist_ctx)
        self._post_run_checklist = result.to_dict()
        self._write_json(self.gov_dir / "post_run_checklist.json",
                         self._post_run_checklist)
        self.gov_audit.record(
            GA.CHECKLIST_COMPLETED,
            decision="passed" if result.passed else "failed",
            reason="post-run checklist",
            metadata={"failed_required": result.failed_required})

        # ClaimGuard scan of the final operator-facing report.
        scan = self.governance.claim_guard.scan_text(status.to_markdown())
        self._claim_guard_report = scan.to_dict()
        self._write_json(self.gov_dir / "claim_guard_report.json",
                         self._claim_guard_report)
        if not scan.safe:
            self.incidents.record(
                I.POLICY_VIOLATION, "warning",
                f"{len(scan.findings)} unsupported claim(s) flagged in the "
                "final report",
                related_metric="claim_guard",
                suggested_debug_step="see claim_guard_report.json")

        # Post-run review: a recommendation for a human, never an action.
        violations = [v.to_dict()
                      for v in (self._policy_decision.violations
                                if self._policy_decision else [])]
        approvals_used = ([r.to_dict()
                           for r in self.approvals.list_by_status(APPROVED)]
                          if self.approvals else [])
        plasticity = self._health_snapshot().get("plasticity")
        reviewer = (self.operator_session.operator.name
                    if self.operator_session else "")
        review = PostRunReview(run_id=m.run_id, reviewer=reviewer).build(
            status=status.to_dict(),
            incidents=self.incidents.list_incidents(),
            policy_violations=violations,
            approvals_used=approvals_used,
            plasticity_changes=plasticity,
            emergency_stop_used=self._emergency_stop_triggered
            or self.emergency.requested)
        self._post_run_review = review.to_dict()
        self._write_json(self.gov_dir / "post_run_review.json",
                         self._post_run_review)

        if self.approvals is not None and self.approvals.path is not None:
            self.approvals.save()
        if self.operator_session is not None:
            self._write_json(self.gov_dir / "operator_session.json",
                             self.operator_session.to_dict())

    def governance_summary(self) -> Dict[str, Any]:
        """Governance status for the Inner MAP / status report."""
        if self.governance is None:
            return {"enabled": False,
                    "emergency_stop_available": True,
                    "emergency_stop_requested": self.emergency.requested}
        risk = self.risk_assessment
        decision = self._policy_decision
        last_violation = (decision.violations[-1].to_dict()
                          if decision and decision.violations else None)
        claim_status = None
        if self._claim_guard_report is not None:
            claim_status = ("safe" if self._claim_guard_report.get("safe")
                            else "warnings")
        return {
            "enabled": True,
            "policy_status": ("refused" if self._governance_refused
                              else "allowed" if decision is not None
                              else "not_evaluated"),
            "risk_level": risk.overall_level if risk else "unassessed",
            "active_permissions":
                self.governance.permissions.granted_scopes(),
            "approval_count": (len(self.approvals.list_by_status(APPROVED))
                               if self.approvals else 0),
            "pending_approval_count": (len(self.approvals.list_pending())
                                       if self.approvals else 0),
            "expired_approval_count": (self.approvals.expired_count()
                                       if self.approvals else 0),
            "emergency_stop_available": True,
            "emergency_stop_requested": self._emergency_stop_triggered
            or self.emergency.requested,
            "policy_violation_count": (len(decision.violations)
                                       if decision else 0),
            "last_policy_violation": last_violation,
            "refusal_reasons": list(self._refusal_reasons) or None,
            "governance_audit_path": str(self.gov_audit.path),
            "operator_session": (self.operator_session.to_dict()
                                 if self.operator_session else None),
            "runbook_path": None,  # runbooks are generated separately
            "claim_guard_status": claim_status,
            "pre_run_checklist_passed": (self._pre_run_checklist or {}).get(
                "passed"),
            "post_run_review_recommendation": (
                self._post_run_review or {}).get("recommendation"),
        }

    # -- snapshots ---------------------------------------------------------------

    def _health_snapshot(self) -> Dict[str, Any]:
        runner = self._last_runner
        snapshot: Dict[str, Any] = {
            "now": time.time(),
            "state_dir": self.manifest.state_dir,
            "artifact_dir": str(self.ops_dir),
        }
        if runner is None:
            return snapshot
        bridge = getattr(runner, "bridge", None)
        if bridge is not None:
            telemetry = dict(bridge.telemetry.report())
            # Segmented supervision: each segment is a fresh runner, so session
            # counters reset per segment. Progress is keyed on the monotone
            # lifetime counter instead, so the "still increasing" health checks
            # see the supervised session, not one slice of it.
            lifetime = telemetry.get("lifetime_steps", telemetry.get("steps", 0))
            for counter in ("events", "reservoir_updates", "trace_event_count"):
                telemetry[counter] = lifetime  # strictly monotone across segments
            snapshot["telemetry"] = telemetry
            snapshot["substrate"] = bridge.substrate.metrics().to_dict() | {
                "state_size": bridge.substrate.state_size}
            if getattr(bridge, "meaning_trace_builder", None) is not None:
                snapshot["language"] = {
                    "meaning_atoms": len(bridge.meaning_trace_builder)}
        lifecycle = getattr(runner, "lifecycle", None)
        if lifecycle is not None:
            lc = lifecycle.snapshot()
            # Between segments the segment runner has (gracefully) died; the
            # supervised session itself is alive until the supervisor stops.
            session_alive = not self._finalized and (
                not self._stop_requested or lc.get("graceful", True))
            snapshot["lifecycle"] = lc | {
                "alive": session_alive,
                "state": (f"supervised({lc.get('state', 'unknown')})"
                          if session_alive else lc.get("state")),
                "last_checkpoint_ts": getattr(runner, "_last_checkpoint_ts",
                                              0.0),
            }
        engine = getattr(runner, "plasticity_engine", None)
        if engine is not None:
            snapshot["plasticity"] = engine.snapshot()
        if hasattr(runner, "embodiment_summary"):
            snapshot["embodiment"] = runner.embodiment_summary()
        latent = getattr(runner, "latent", None)
        if latent is not None:
            snapshot["latent"] = latent.summary()
        homeostasis = getattr(runner, "homeostasis", None)
        if homeostasis is not None:
            snapshot["homeostasis"] = homeostasis.summary()
        executive = getattr(runner, "executive", None)
        if executive is not None:
            snapshot["executive"] = executive.summary()
        ego = getattr(runner, "ego", None)
        if ego is not None:
            snapshot["ego"] = ego.summary()
        communication = getattr(runner, "communication", None)
        if communication is not None:
            snapshot["communication"] = communication.summary()
        developmental = getattr(runner, "developmental", None)
        if developmental is not None:
            snapshot["developmental"] = developmental.summary()
        nursery = getattr(runner, "nursery", None)
        if nursery is None and developmental is not None:
            nursery = getattr(developmental, "nursery", None)
        if nursery is not None:
            snapshot["ecology"] = nursery.summary()
            snapshot["ecology_snapshot"] = {
                "memory": nursery.memory.snapshot(),
                "stream": nursery.stream.snapshot(),
            }
        active_perception = getattr(runner, "active_perception", None)
        if active_perception is None and developmental is not None:
            active_perception = getattr(developmental, "active_perception",
                                        None)
        if active_perception is not None and hasattr(active_perception,
                                                     "snapshot"):
            snapshot["active_perception"] = active_perception.snapshot()
        hypothesis = getattr(runner, "hypothesis_engine", None)
        if hypothesis is None and developmental is not None:
            hypothesis = getattr(developmental, "hypothesis_engine", None)
        if hypothesis is not None and hasattr(hypothesis, "snapshot"):
            snapshot["hypothesis"] = hypothesis.snapshot()
        autoregen = getattr(runner, "autoregeneration", None)
        if autoregen is None and developmental is not None:
            autoregen = getattr(developmental, "autoregeneration", None)
        if autoregen is not None and hasattr(autoregen, "snapshot"):
            snapshot["autoregeneration"] = autoregen.snapshot()
        logos = getattr(runner, "logos", None)
        if logos is None and developmental is not None:
            logos = getattr(developmental, "logos", None)
        if logos is not None and hasattr(logos, "snapshot"):
            snapshot["logos"] = logos.snapshot()
        conscience = getattr(runner, "conscience", None)
        if conscience is not None and hasattr(conscience, "summary"):
            snapshot["conscience"] = {
                "summary": conscience.summary(),
                "snapshot": (conscience.snapshot()
                             if hasattr(conscience, "snapshot") else {}),
                "emergency_requested": getattr(
                    conscience, "emergency_requested", False),
            }
        pilot = getattr(runner, "pilot1", None) or getattr(runner, "pilot",
                                                           None)
        if pilot is not None and isinstance(pilot, dict):
            snapshot["pilot1"] = pilot
        elif pilot is not None and hasattr(pilot, "pilot_status"):
            snapshot["pilot1"] = pilot.pilot_status()
        membrane = getattr(runner, "sensory_membrane", None)
        if membrane is not None and isinstance(membrane, dict):
            snapshot["sensory_membrane"] = membrane
        elif membrane is not None and hasattr(membrane, "summary"):
            snapshot["sensory_membrane"] = membrane.summary()
        pilot2 = getattr(runner, "pilot2", None)
        if pilot2 is not None and isinstance(pilot2, dict):
            snapshot["pilot2"] = pilot2
        elif pilot2 is not None and hasattr(pilot2, "pilot2_status"):
            snapshot["pilot2"] = pilot2.pilot2_status()
        motor = getattr(runner, "motor_membrane", None)
        if motor is not None and isinstance(motor, dict):
            snapshot["motor_membrane"] = motor
        elif motor is not None and hasattr(motor, "summary"):
            snapshot["motor_membrane"] = motor.summary()
        pilot3 = getattr(runner, "pilot3", None)
        if pilot3 is not None and isinstance(pilot3, dict):
            snapshot["pilot3"] = pilot3
        elif pilot3 is not None and hasattr(pilot3, "pilot3_status"):
            snapshot["pilot3"] = pilot3.pilot3_status()
        pilot4 = getattr(runner, "pilot4", None)
        if pilot4 is not None and isinstance(pilot4, dict):
            snapshot["pilot4"] = pilot4
        elif pilot4 is not None and hasattr(pilot4, "pilot4_status"):
            snapshot["pilot4"] = pilot4.pilot4_status()
        safety = getattr(runner, "safety_invariants", None)
        if safety is not None and isinstance(safety, dict):
            snapshot["safety_invariants"] = safety
        elif safety is not None and hasattr(safety, "safety_invariant_status"):
            snapshot["safety_invariants"] = safety.safety_invariant_status()
        elif safety is not None and hasattr(safety, "snapshot"):
            snapshot["safety_invariants"] = safety.snapshot()
        research = getattr(runner, "research_lab", None)
        if research is not None and isinstance(research, dict):
            snapshot["research_lab"] = research
        elif research is not None and hasattr(research, "research_lab_status"):
            snapshot["research_lab"] = research.research_lab_status()
        elif research is not None and hasattr(research, "snapshot"):
            snapshot["research_lab"] = research.snapshot()
        return snapshot

    def pilot2_status(self) -> Dict[str, Any]:
        """Expose Pilot-2 read-only soak status (if any)."""
        p = self._health_snapshot().get("pilot2") or {}
        return {
            "pilot2_enabled": p.get("enabled", p.get("pilot2_enabled", False)),
            "pilot2_phase": p.get("pilot2_phase", p.get("current_phase")),
            "source_count": p.get("source_count", 0),
            "reliable_source_count": p.get("reliable_source_count", 0),
            "unsafe_source_count": p.get("unsafe_source_count", 0),
            "source_reliability_summary": p.get("source_reliability_summary",
                                                {}),
            "latest_source_preflight": p.get("latest_source_preflight"),
            "latest_daily_review": p.get("latest_daily_review"),
            "latest_weekly_review": p.get("latest_weekly_review"),
            "latest_grounding_quality": p.get("latest_grounding_quality"),
            "recommendation": p.get("recommendation"),
        }

    def motor_status(self) -> Dict[str, Any]:
        """Expose Pilot-3 motor membrane status (if any).

        The motor membrane is simulation/dry-run only; this exposes counts and
        the firewall state so the operator can confirm no real-world action
        occurred. ``real_world_authority`` is always ``False`` and the firewall
        cannot be disabled.
        """
        m = self._health_snapshot().get("motor_membrane") or {}
        return {
            "motor_membrane_enabled": m.get("enabled", False),
            "embodiment_profile": m.get("profile_id"),
            "real_world_authority": m.get("real_world_authority", False),
            "action_count": m.get("action_count", 0),
            "simulated_action_count": m.get("simulated_action_count", 0),
            "veto_count": m.get("veto_count", 0),
            "blocked_real_world_count": m.get("blocked_real_world_count", 0),
            "firewall_enabled": m.get("firewall_enabled", True),
            "firewall_can_be_disabled": m.get("firewall_can_be_disabled",
                                              False),
            "latest_firewall_decision": m.get("latest_firewall_decision"),
            "sandbox_health": m.get("sandbox_health"),
            "ledger_write_failures": m.get("ledger_write_failures", 0),
            "action_ledger_path": m.get("action_ledger_path"),
            "pilot3_report_path": m.get("pilot3_report_path"),
        }

    def pilot3_status(self) -> Dict[str, Any]:
        """Expose Pilot-3 simulated embodiment soak status (if any).

        Pilot-3 is simulation/dry-run only; this exposes the soak phase,
        embodiment condition, action counts, firewall-audit status, latest
        action-grounding quality, the latest report path, and the
        non-actuation proof status. No real-world action ever occurs.
        """
        snap = self._health_snapshot()
        p = snap.get("pilot3") or {}
        motor = snap.get("motor_membrane") or {}
        return {
            "pilot3_soak_enabled": p.get("enabled", p.get("pilot3_soak_enabled",
                                                          bool(p))),
            "pilot3_soak_phase": p.get("pilot3_soak_phase",
                                       p.get("current_phase")),
            "embodiment_condition": p.get("embodiment_condition",
                                          motor.get("profile_id")),
            "action_count": p.get("action_count",
                                  motor.get("action_count", 0)),
            "simulated_action_count": p.get(
                "simulated_action_count",
                motor.get("simulated_action_count", 0)),
            "veto_count": p.get("veto_count", motor.get("veto_count", 0)),
            "firewall_audit_status": p.get("firewall_audit_status"),
            "firewall_audit_critical_findings": p.get(
                "firewall_audit_critical_findings", 0),
            "latest_action_grounding_quality": p.get(
                "latest_action_grounding_quality"),
            "sandbox_overfit_warning": p.get("sandbox_overfit_warning", False),
            "latest_pilot3_report_path": p.get("latest_pilot3_report_path"),
            "non_actuation_proof_status": p.get(
                "non_actuation_proof_status",
                "no real-world action; firewall enabled"
                if motor.get("firewall_enabled", True) else "firewall not "
                "enabled"),
            "real_world_authority": False,
        }

    def pilot4_status(self) -> Dict[str, Any]:
        """Expose Pilot-4 planning-only readiness status (if any).

        Pilot-4 is planning-only; this exposes whether planning is enabled, the
        readiness dossier path, the decision-gate recommendation, the forbidden
        actuator registry status, and the risk-assessment status.
        ``real_world_actuation_enabled`` is always ``False``.
        """
        p = self._health_snapshot().get("pilot4") or {}
        return {
            "pilot4_planning_enabled": p.get("enabled",
                                             p.get("pilot4_planning_enabled",
                                                   bool(p))),
            "current_planning_phase": p.get("current_planning_phase",
                                            p.get("current_phase")),
            "readiness_dossier_path": p.get("readiness_dossier_path"),
            "decision_gate_recommendation": p.get(
                "decision_gate_recommendation"),
            "readiness_conclusion": p.get("readiness_conclusion"),
            "real_world_actuation_enabled": False,
            "forbidden_actuator_count": p.get("forbidden_actuator_count", 0),
            "forbidden_actuator_registry_status": p.get(
                "forbidden_actuator_registry_status", "active"),
            "risk_assessment_status": p.get("risk_assessment_status"),
        }

    def safety_invariant_status(self) -> Dict[str, Any]:
        """Expose the system-wide safety invariant status (if any).

        Safety checks are read-only/inert; this exposes the latest fast/full
        check, the latest red-team result, any critical failure, the assurance
        case path, the dashboard path, and the unresolved blocker count. Safety
        checks cannot be disabled by runtime modules.
        """
        s = self._health_snapshot().get("safety_invariants") or {}
        return {
            "safety_invariant_runner_enabled": s.get(
                "enabled", s.get("safety_invariant_runner_enabled", bool(s))),
            "latest_fast_check": s.get("latest_fast_check"),
            "latest_full_check": s.get("latest_full_check"),
            "latest_red_team_result": s.get("latest_red_team_result"),
            "latest_critical_failure": s.get("latest_critical_failure"),
            "critical_failure_count": s.get("critical_failure_count", 0),
            "assurance_case_path": s.get("assurance_case_path"),
            "safety_dashboard_path": s.get("safety_dashboard_path"),
            "unresolved_blocker_count": s.get("unresolved_blocker_count", 0),
            "can_be_disabled": False,
        }

    def research_lab_status(self) -> Dict[str, Any]:
        """Expose the research-lab status (if any).

        The research lab is a bounded measurement instrument: this exposes the
        current experiment/variant, the latest result/comparison/report paths,
        and the unsafe/inconclusive experiment counts. It holds no external
        authority and starts no long runs.
        """
        r = self._health_snapshot().get("research_lab") or {}
        return {
            "research_lab_enabled": r.get("enabled",
                                          r.get("research_lab_enabled",
                                                bool(r))),
            "current_experiment_id": r.get("current_experiment_id"),
            "current_variant": r.get("current_variant"),
            "latest_result_path": r.get("latest_result_path"),
            "latest_comparison_path": r.get("latest_comparison_path"),
            "latest_research_report_path": r.get("latest_research_report_path"),
            "unsafe_experiment_count": r.get("unsafe_experiment_count", 0),
            "inconclusive_experiment_count": r.get(
                "inconclusive_experiment_count", 0),
        }

    def membrane_status(self) -> Dict[str, Any]:
        """Expose read-only sensory membrane status (if any)."""
        m = self._health_snapshot().get("sensory_membrane") or {}
        return {
            "sensory_membrane_enabled": m.get("enabled", False),
            "source_count": m.get("source_count", 0),
            "healthy_source_count": m.get("healthy_source_count", 0),
            "degraded_source_count": m.get("degraded_source_count", 0),
            "events_per_minute": m.get("events_per_minute", 0.0),
            "dropped_events": m.get("dropped_events", 0),
            "malformed_events": m.get("malformed_events", 0),
            "membrane_report_path": m.get("membrane_report_path"),
            "read_only_violation_count": m.get("read_only_violation_count", 0),
        }

    def pilot_status(self) -> Dict[str, Any]:
        """Expose Pilot-1 status from the latest health snapshot (if any)."""
        pilot = self._health_snapshot().get("pilot1") or {}
        return {
            "pilot_mode": pilot.get("pilot_mode", pilot.get("mode")),
            "pilot_phase": pilot.get("pilot_phase",
                                     pilot.get("current_phase")),
            "elapsed_seconds": pilot.get("elapsed_seconds"),
            "uptime_ratio": pilot.get("uptime_ratio"),
            "dashboard_path": pilot.get("dashboard_path"),
            "daily_review_path": pilot.get("daily_review_path"),
            "weekly_review_path": pilot.get("weekly_review_path"),
            "latest_incident": pilot.get("latest_incident"),
            "exit_recommendation": pilot.get("exit_recommendation"),
            "active_failure_modes": pilot.get("active_failure_modes", []),
        }

    def _build_status(self) -> OperationalStatus:
        snapshot = self._health_snapshot()
        return OperationalStatus(
            manifest=self.manifest.to_dict(),
            lifecycle=snapshot.get("lifecycle"),
            telemetry=snapshot.get("telemetry"),
            health=self._last_health,
            watchdog=self.watchdog.snapshot(),
            budget=self.budget.to_dict(),
            incidents=self.incidents.list_incidents(),
            artifacts={"ops_dir": str(self.ops_dir),
                       "bytes": directory_bytes(self.ops_dir),
                       "rotation": self.rotation.report or None},
            governance=self.governance_summary(),
        )

    def _status_provider(self) -> Dict[str, Any]:
        status = self._build_status()
        return {
            "health": status.health,
            "status": {"compact": status.compact_line(),
                       **status.to_dict()},
            "manifest": status.manifest,
            "latest_report": status.to_markdown(),
            "incidents": status.incidents,
        }

    # -- control ---------------------------------------------------------------------

    def stop(self, reason: str) -> None:
        """Operator stop request; honoured at the next segment boundary."""
        self._stop_requested = True
        self.shutdown_manager.request_shutdown(reason)

    def snapshot(self) -> Dict[str, Any]:
        return self._build_status().to_dict()

    def finalize(self, graceful: bool = True, note: str = "") -> None:
        """Write final evidence, rotate artifacts, close everything. Idempotent."""
        if self._finalized:
            return
        self._finalized = True
        m = self.manifest
        status = self._build_status()
        self._write_json(self.ops_dir / "status.json", status.to_dict())
        (self.ops_dir / "status.md").write_text(status.to_markdown(),
                                                encoding="utf-8")
        try:
            rotation_report = self.rotation.rotate()
        except Exception as exc:
            rotation_report = {"errors": [str(exc)]}
            self.incidents.record(I.ROTATION_FAILURE, "warning", str(exc))
        self._write_json(self.ops_dir / "artifact_rotation.json",
                         rotation_report)
        inner_map = None
        observer = getattr(self._last_runner, "observer", None)
        if observer is not None:
            try:
                inner_map = observer.update().to_dict()
            except Exception:  # final snapshot is best-effort
                inner_map = None
        reason = (self.shutdown_manager.snapshot().get("reason")
                  or note or "session complete")
        if not self.shutdown_manager.requested:
            self.shutdown_manager.request_shutdown(reason)
        self.shutdown_manager.perform_shutdown(
            runner=None,  # segments already stopped at their bounds
            health_report=self._last_health,
            inner_map=inner_map,
            final_report_md=status.to_markdown())
        self.registry.register_stop(m.run_id, graceful=graceful, summary={
            "last_health": (self._last_health or {}).get("level"),
            "incident_count": len(self.incidents.list_incidents()),
        })
        if self.governance is not None:
            try:
                self._governance_post_run(status)
            except Exception as exc:  # evidence is best-effort at shutdown
                logger.warning("governance post-run failed: %s", exc)
        if self.status_server is not None:
            self.status_server.stop()
        self.incidents.close()
        if self.gov_audit is not None:
            self.gov_audit.close()

    # -- helpers -----------------------------------------------------------------------

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)

    @staticmethod
    def _append_jsonl(path: Path, row: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")

    # -- Inner MAP hook -------------------------------------------------------------------

    def operations_summary(self) -> Dict[str, Any]:
        """Compact ops status for the Inner MAP."""
        last_incident = self.incidents.last()
        return {
            "run_mode": self.manifest.mode,
            "health_level": (self._last_health or {}).get("level", "unknown"),
            "watchdog_stop_requested": self.watchdog.should_stop(),
            "budget_within": self.budget.within_budget(),
            "incident_count": len(self.incidents.list_incidents()),
            "last_incident": (last_incident or {}).get("type"),
            "graceful_shutdown_requested": self.shutdown_manager.requested,
            "artifact_rotation": bool(self.rotation.report),
            "local_status_server": (self.status_server.snapshot()
                                    if self.status_server else
                                    {"enabled": False}),
            "soak_stage": (self.manifest.mode
                           if self.manifest.mode in RunMode.SOAK_MODES
                           else None),
            "governance": self.governance_summary(),
        }
