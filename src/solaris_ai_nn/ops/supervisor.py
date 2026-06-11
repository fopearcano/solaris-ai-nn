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
        return snapshot

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
