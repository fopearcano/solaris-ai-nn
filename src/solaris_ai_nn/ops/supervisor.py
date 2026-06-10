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
        enable_plasticity=manifest.enabled_features.get("plasticity", False))


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

    _stop_requested: bool = field(default=False, init=False)
    _segments_run: int = field(default=0, init=False)
    _last_health: Optional[Dict[str, Any]] = field(default=None, init=False)
    _last_runner: Any = field(default=None, init=False)
    _started_at: float = field(default=0.0, init=False)
    _finalized: bool = field(default=False, init=False)

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
        self._write_json(self.ops_dir / "manifest.json", m.to_dict())

    # -- main loop ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Run the supervised session; returns the final status dict."""
        m = self.manifest
        self._started_at = time.time()
        self.registry.register_start(m)
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
        if self.status_server is not None:
            self.status_server.stop()
        self.incidents.close()

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
        }
