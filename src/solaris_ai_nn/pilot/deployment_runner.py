"""PilotDeploymentRunner -- one governed, supervised, bounded pilot.

The runner is the only sanctioned way to deploy: it loads the profile,
gates the manifest through :class:`PilotSafetyValidator` and the governance
policy (via the OperationalSupervisor's own pre-run gate), runs the bounded
pilot under full supervision, and ends with a registry entry, a readiness
report, an input summary, a ClaimGuard-scanned pilot report, and a
recommendation. An unsafe manifest is refused, never repaired.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..governance.operator import OperatorProfile, OperatorSession
from ..governance.risk import RiskLevel, assess_manifest
from ..ops.run_manifest import OperationalRunManifest
from ..ops.run_registry import RunRegistry
from ..ops.supervisor import OperationalSupervisor
from ..utils.logging import get_logger
from .adapters import (
    ReadOnlyStreamPilotAdapter,
    SimulatedPilotAdapter,
    SolarisSidecarPilotAdapter,
)
from .pilot_manifest import PilotManifest
from .pilot_registry import PilotRegistry
from .pilot_report import PilotReportBuilder
from .profiles import PilotProfileRegistry, PilotProfileType
from .readiness import PilotReadinessCheck, PilotReadinessReport
from .safety import PilotSafetyValidator

logger = get_logger(__name__)


@dataclass
class PilotDeploymentRunner:
    """Prepare, run, and account for one Pilot-0 deployment."""

    manifest: PilotManifest
    profile_registry: PilotProfileRegistry = field(
        default_factory=PilotProfileRegistry.default)
    safety: Optional[PilotSafetyValidator] = None
    operator_session: Optional[OperatorSession] = None
    approvals: Any = None                 # optional ApprovalRegistry
    registry: Optional[PilotRegistry] = None
    governance_dir: Optional[str] = None
    approved_output_roots: Optional[List[str]] = None
    readiness_context: Dict[str, Any] = field(default_factory=dict)
    # Sidecar profile inputs (fake or real conscience; optional demo driver).
    conscience: Any = None
    sidecar_driver: Optional[Callable[[Any, int], None]] = None

    _prepared: bool = field(default=False, init=False)
    _refused: bool = field(default=False, init=False)
    _refusal_reasons: List[str] = field(default_factory=list, init=False)
    _finalized: bool = field(default=False, init=False)
    _status: Optional[Dict[str, Any]] = field(default=None, init=False)

    def __post_init__(self) -> None:
        m = self.manifest
        self.profile = self.profile_registry.get(m.profile)
        if self.safety is None:
            self.safety = PilotSafetyValidator(
                profile_registry=self.profile_registry)
        if self.operator_session is None:
            self.operator_session = OperatorSession(
                operator=OperatorProfile(name=m.operator or "unnamed"),
                active_run_id=m.run_id)
        if self.registry is None:
            self.registry = PilotRegistry(
                Path(m.artifact_dir) / "pilot_registry.json")
        self.pilot_dir = Path(m.artifact_dir) / "runs" / m.pilot_id
        self.adapter = self._build_adapter()
        self.supervisor: Optional[OperationalSupervisor] = None
        self.safety_report = None
        self.readiness_report: Optional[PilotReadinessReport] = None
        self.report_paths: Dict[str, Any] = {}

    # -- adapter / supervisor construction -------------------------------------

    def _build_adapter(self) -> Any:
        m = self.manifest
        if m.profile == PilotProfileType.SIMULATED:
            return SimulatedPilotAdapter(manifest=m)
        if m.profile == PilotProfileType.READ_ONLY_STREAM:
            return ReadOnlyStreamPilotAdapter(manifest=m)
        return SolarisSidecarPilotAdapter(
            manifest=m, conscience=self.conscience,
            driver=self.sidecar_driver)

    def _ops_manifest(self) -> OperationalRunManifest:
        m = self.manifest
        steps = m.max_steps or self.profile.default_max_steps
        features = {
            "plasticity": m.enabled_features.get("plasticity", False),
            "plasticity_dry_run": m.enabled_features.get(
                "plasticity_dry_run", False),
            "embodiment": m.profile == PilotProfileType.SIMULATED,
            "language": m.enabled_features.get("language", False),
            "sidecar": m.profile == PilotProfileType.SOLARIS_SIDECAR_OBSERVE,
            "evaluation": False,
            "local_status_server": m.enabled_features.get(
                "local_status_server", False),
        }
        return OperationalRunManifest(
            mode="bounded", max_steps=steps,
            max_duration_s=m.max_duration_s,
            state_dir=m.state_dir,
            artifact_dir=str(self.pilot_dir / "ops"),
            substrate=m.substrate, seed=m.seed,
            healthcheck_interval_steps=max(25, steps // 4),
            enabled_features=features,
            operator_notes=f"pilot {m.pilot_id} ({m.profile}): {m.notes}",
            run_id=m.run_id, session_id=m.session_id)

    # -- operator actions ---------------------------------------------------------

    def assess_risks(self):
        """The pilot's risk assessment (with pilot-profile context)."""
        return assess_manifest(self._ops_manifest().to_dict(),
                               {"run_id": self.manifest.run_id,
                                "pilot_profile": self.manifest.profile})

    def acknowledge_risks(self, note: str = "reviewed by operator",
                          ) -> List[str]:
        """Operator action: acknowledge each medium risk by name.

        This is the explicit human step -- call it from operator-driven code
        after showing the assessment, never from automation that has not
        displayed the risks.
        """
        acknowledged: List[str] = []
        for item in self.assess_risks().items_at(RiskLevel.MEDIUM):
            self.operator_session.acknowledge_risk(item.name, note=note)
            acknowledged.append(item.name)
        return acknowledged

    # -- lifecycle ----------------------------------------------------------------

    def prepare(self) -> Dict[str, Any]:
        """Safety + readiness gates; build the supervisor; write the record."""
        m = self.manifest
        context = {"approved_output_roots": self.approved_output_roots or []}
        self.safety_report = self.safety.validate_manifest(m, context)
        self._write_json(self.pilot_dir / "pilot_manifest.json", m.to_dict())
        self._write_json(self.pilot_dir / "safety_contract.json",
                         {"contract": m.contract.to_dict(),
                          "statements": m.contract.statements()})

        if not self.safety_report.safe:
            self._refused = True
            self._refusal_reasons = list(self.safety_report.violations)
            self._write_json(self.pilot_dir / "safety_report.json",
                             self.safety_report.to_dict())
            return {"prepared": False, "reasons": self._refusal_reasons}

        self.supervisor = OperationalSupervisor(
            manifest=self._ops_manifest(),
            runner_factory=lambda _m, steps: self.adapter.build_runner(steps),
            registry=RunRegistry(self.pilot_dir / "ops_run_registry.json"),
            operator_session=self.operator_session,
            approvals=self.approvals,
            governance_dir=self.governance_dir
            or str(self.pilot_dir / "governance"))

        readiness = PilotReadinessCheck(
            manifest=m, profile_registry=self.profile_registry,
            safety=self.safety, governance=self.supervisor.governance,
            approvals=self.supervisor.approvals,
            operator_session=self.operator_session)
        ctx = dict(self.readiness_context)
        ctx.setdefault("approved_output_roots",
                       self.approved_output_roots or [])
        self.readiness_report = readiness.run(ctx)
        self._write_json(self.pilot_dir / "readiness_report.json",
                         self.readiness_report.to_dict())
        (self.pilot_dir / "readiness_report.md").write_text(
            self.readiness_report.to_markdown(), encoding="utf-8")

        self._prepared = True
        return {"prepared": True,
                "ready": self.readiness_report.ready,
                "reasons": [i.detail for i in
                            self.readiness_report.blocking_issues()]}

    def run(self) -> Dict[str, Any]:
        """Run the bounded pilot end to end; returns the final snapshot."""
        if not self._prepared and not self._refused:
            self.prepare()
        m = self.manifest
        if self._refused:
            self.registry.register_start(m)
            self.registry.register_stop(
                m.pilot_id, status="refused",
                readiness_status="unsafe",
                final_recommendation="reduce_scope")
            return self.snapshot()

        entry = self.registry.register_start(m)
        self.registry.register_update(
            m.pilot_id,
            readiness_status="ready" if self.readiness_report.ready
            else "not_ready")
        status = self.supervisor.run()
        self._status = status
        governance = status.get("governance") or {}
        if governance.get("policy_status") == "refused":
            # The governance gate inside the supervisor said no.
            self._refused = True
            self._refusal_reasons = list(
                governance.get("refusal_reasons") or [])
            self.registry.register_stop(
                m.pilot_id, status="refused",
                final_recommendation="reduce_scope",
                incident_count=int(status.get("incident_count", 0) or 0))
            return self.snapshot()

        self._post_run(status)
        return self.snapshot()

    def _post_run(self, status: Dict[str, Any]) -> None:
        """Input summary, Inner MAP, pilot report, artifacts, registry stop."""
        m = self.manifest
        input_summary = self.adapter.input_summary()
        self._write_json(self.pilot_dir / "input_summary.json", input_summary)

        # Inner MAP: the last segment runner's observer, now seeing the pilot.
        runner = getattr(self.supervisor, "_last_runner", None)
        observer = getattr(runner, "observer", None)
        if observer is not None:
            observer.pilot = self
            try:
                self._write_json(self.pilot_dir / "pilot_inner_map.json",
                                 observer.update().to_dict())
            except Exception:  # final snapshot is best-effort
                pass

        ingestion = (input_summary.get("sensors")
                     and {"sensors": input_summary["sensors"]}) or None
        embodiment = None
        if m.profile == PilotProfileType.SIMULATED \
                and hasattr(runner, "embodiment_summary"):
            embodiment = runner.embodiment_summary()
        sidecar = None
        if m.profile == PilotProfileType.SOLARIS_SIDECAR_OBSERVE \
                and getattr(self.adapter, "sidecar", None) is not None:
            sidecar = self.adapter.sidecar.integration_summary()

        builder = PilotReportBuilder(m)
        report = builder.build(
            status=status,
            readiness=(self.readiness_report.to_dict()
                       if self.readiness_report else None),
            input_summary=input_summary, ingestion=ingestion,
            embodiment=embodiment, sidecar=sidecar)
        self.report_paths = builder.save(
            report,
            self.pilot_dir / "pilot_report.json",
            self.pilot_dir / "pilot_report.md")
        recommendation = report.report.metadata.get("recommendation")

        artifacts = sorted(str(p.relative_to(self.pilot_dir))
                           for p in self.pilot_dir.rglob("*") if p.is_file())
        self._write_json(self.pilot_dir / "artifacts.json", {
            "pilot_dir": str(self.pilot_dir),
            "files": artifacts,
            "expected": self.profile.required_artifacts,
            "missing": [a for a in self.profile.required_artifacts
                        if a not in artifacts],
        })
        self.registry.register_stop(
            m.pilot_id, status="completed",
            incident_count=int(status.get("incident_count", 0) or 0),
            final_recommendation=recommendation,
            report_path=str(self.pilot_dir / "pilot_report.md"))
        self._finalized = True

    def stop(self, reason: str) -> None:
        """Operator stop; honoured at the next supervised boundary."""
        if self.supervisor is not None:
            self.supervisor.stop(reason)

    def finalize(self) -> None:
        """Idempotent: close out the supervisor and the registry entry."""
        if self.supervisor is not None:
            self.supervisor.finalize(graceful=True)
        if not self._finalized and not self._refused and self._status:
            self._post_run(self._status)

    # -- status ---------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pilot_id": self.manifest.pilot_id,
            "profile": self.manifest.profile,
            "prepared": self._prepared,
            "refused": self._refused,
            "refusal_reasons": list(self._refusal_reasons),
            "safety": (self.safety_report.to_dict()
                       if self.safety_report else None),
            "readiness": (self.readiness_report.to_dict()
                          if self.readiness_report else None),
            "input_summary": self.adapter.input_summary(),
            "supervisor": (self._status or
                           (self.supervisor.snapshot()
                            if self.supervisor else None)),
            "report_paths": self.report_paths or None,
            "registry_entry": self.registry.get_pilot(self.manifest.pilot_id),
        }

    def pilot_summary(self) -> Dict[str, Any]:
        """Compact pilot status for the Inner MAP."""
        entry = self.registry.get_pilot(self.manifest.pilot_id) or {}
        input_summary = self.adapter.input_summary()
        ingestion_count = 0
        for sensor in input_summary.get("sensors") or []:
            ingestion_count += int(
                ((sensor.get("source") or sensor).get("ingestion") or {})
                .get("events_accepted", 0))
        return {
            "pilot_mode_active": entry.get("status") == "running",
            "pilot_profile": self.manifest.profile,
            "pilot_readiness_status": entry.get("readiness_status") or (
                "ready" if (self.readiness_report
                            and self.readiness_report.ready) else "unknown"),
            "input_source_count": len(self.manifest.input_sources),
            "stream_ingestion_count": ingestion_count,
            "pilot_safety_status": ("safe" if (self.safety_report
                                               and self.safety_report.safe)
                                    else "blocked" if self.safety_report
                                    else "unchecked"),
            "pilot_incident_count": int(entry.get("incident_count", 0) or 0),
            "pilot_recommendation": entry.get("final_recommendation"),
            "pilot_report_path": entry.get("report_path"),
        }

    # -- helpers ----------------------------------------------------------------------

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
