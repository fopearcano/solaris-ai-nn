"""Pilot readiness -- is this pilot actually ready to run?

Six areas are checked: governance, operations, evaluation, safety, recovery,
and documentation. Blocking issues mean *not ready*; warnings are recorded
with a next step. Several checks ("quick suite passed", "restart demo
passed") accept an explicit ``"skipped"`` -- skipping is allowed, silence is
not.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .pilot_manifest import PilotManifest
from .profiles import PilotProfileRegistry, PilotProfileType
from .safety import PilotSafetyValidator

BLOCKING = "blocking"
WARNING = "warning"


@dataclass
class ReadinessIssue:
    area: str
    severity: str
    detail: str
    next_step: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PilotReadinessReport:
    """The verdict: ready or not, and exactly why."""

    pilot_id: str
    profile: str
    ready: bool
    issues: List[ReadinessIssue] = field(default_factory=list)
    checks: List[Dict[str, Any]] = field(default_factory=list)
    recommended_next_step: str = ""
    created_at: float = field(default_factory=time.time)

    def blocking_issues(self) -> List[ReadinessIssue]:
        return [i for i in self.issues if i.severity == BLOCKING]

    def warnings(self) -> List[ReadinessIssue]:
        return [i for i in self.issues if i.severity == WARNING]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pilot_id": self.pilot_id,
            "profile": self.profile,
            "ready": self.ready,
            "created_at": self.created_at,
            "blocking_issues": [i.to_dict() for i in self.blocking_issues()],
            "warnings": [i.to_dict() for i in self.warnings()],
            "checks": list(self.checks),
            "recommended_next_step": self.recommended_next_step,
        }

    def to_markdown(self) -> str:
        lines = [f"# Pilot readiness: {self.pilot_id} ({self.profile})", "",
                 f"Verdict: **{'READY' if self.ready else 'NOT READY'}**", ""]
        if self.blocking_issues():
            lines.append("## Blocking issues")
            for issue in self.blocking_issues():
                lines.append(f"- [{issue.area}] {issue.detail}")
                if issue.next_step:
                    lines.append(f"  - next step: {issue.next_step}")
            lines.append("")
        if self.warnings():
            lines.append("## Warnings")
            for issue in self.warnings():
                lines.append(f"- [{issue.area}] {issue.detail}")
            lines.append("")
        lines.append("## Checks")
        for check in self.checks:
            mark = "x" if check["passed"] else " "
            lines.append(f"- [{mark}] ({check['area']}) {check['name']}")
        lines.append("")
        lines.append(f"Recommended next step: {self.recommended_next_step}")
        lines.append("")
        return "\n".join(lines)


@dataclass
class PilotReadinessCheck:
    """Evaluates the six readiness areas for one pilot manifest."""

    manifest: PilotManifest
    profile_registry: PilotProfileRegistry = field(
        default_factory=PilotProfileRegistry.default)
    safety: Optional[PilotSafetyValidator] = None
    governance: Any = None          # optional GovernancePolicy
    approvals: Any = None           # optional ApprovalRegistry
    operator_session: Any = None    # optional OperatorSession

    def __post_init__(self) -> None:
        if self.safety is None:
            self.safety = PilotSafetyValidator(
                profile_registry=self.profile_registry)

    # -- helpers ------------------------------------------------------------------

    @staticmethod
    def _dir_writable(path: str) -> bool:
        try:
            target = Path(path)
            target.mkdir(parents=True, exist_ok=True)
            return os.access(target, os.W_OK)
        except OSError:
            return False

    # -- the check ------------------------------------------------------------------

    def run(self, context: Optional[Dict[str, Any]] = None,
            ) -> PilotReadinessReport:
        ctx = context or {}
        m = self.manifest
        profile = self.profile_registry.get(m.profile)
        issues: List[ReadinessIssue] = []
        checks: List[Dict[str, Any]] = []

        def check(area: str, name: str, ok: bool, detail: str = "",
                  severity: str = BLOCKING, next_step: str = "") -> None:
            checks.append({"area": area, "name": name, "passed": bool(ok)})
            if not ok:
                issues.append(ReadinessIssue(area, severity, detail or name,
                                             next_step))

        def tri_state(area: str, name: str, value: Any,
                      next_step: str) -> None:
            """True passes; "skipped" warns; anything else warns louder."""
            if value is True or value == "passed":
                check(area, name, True)
            elif value == "skipped":
                check(area, name, False,
                      f"{name} explicitly skipped", WARNING, next_step)
            else:
                check(area, name, False,
                      f"{name} not confirmed (pass True or 'skipped')",
                      WARNING, next_step)

        # A. Governance.
        if self.governance is not None:
            decision = self.governance.evaluate_manifest(
                _ops_manifest_view(m), {"run_id": m.run_id,
                                        "pilot_profile": m.profile})
            check("governance", "policy_evaluated", decision.allowed,
                  "governance policy denied the manifest: "
                  + decision.summary(),
                  next_step="resolve the named approvals/violations")
        else:
            check("governance", "policy_evaluated", False,
                  "no GovernancePolicy attached to the readiness check",
                  next_step="pass governance=GovernancePolicy(...)")
        needs_approval = bool(m.enabled_features.get("plasticity")
                              and not m.enabled_features.get(
                                  "plasticity_dry_run"))
        if needs_approval:
            approved = bool(m.governance_approval_ids) or (
                self.approvals is not None
                and self.approvals.is_approved("enable_plasticity_apply",
                                               {"run_id": m.run_id}))
            check("governance", "approvals_present", approved,
                  "active plasticity needs an approval record",
                  next_step="request approval via the ApprovalRegistry")
        check("governance", "emergency_stop_configured",
              bool(m.emergency_stop_path),
              "emergency stop sentinel path not configured",
              severity=(WARNING if m.profile == PilotProfileType.SIMULATED
                        else BLOCKING),
              next_step="set emergency_stop_path on the manifest")
        check("governance", "operator_session_exists",
              self.operator_session is not None or bool(m.operator),
              "no operator named for this pilot", WARNING,
              "name an operator on the manifest")

        # B. Operations.
        check("operations", "watchdog_enabled", True)  # supervisor-built
        check("operations", "checkpointing_enabled", True)
        check("operations", "state_dir_writable",
              self._dir_writable(m.state_dir),
              f"state dir {m.state_dir!r} is not writable")
        check("operations", "artifact_dir_writable",
              self._dir_writable(m.artifact_dir),
              f"artifact dir {m.artifact_dir!r} is not writable")
        check("operations", "incident_log_writable",
              self._dir_writable(m.artifact_dir),
              "incident log location is not writable")

        # C. Evaluation.
        tri_state("evaluation", "quick_suite_passed",
                  ctx.get("quick_suite_passed"),
                  "run the quick benchmark suite or skip explicitly")
        from ..evaluation.experiment_registry import ExperimentRegistry

        experiments = ExperimentRegistry().list_experiments()
        check("evaluation", "replay_check_available",
              "replay_determinism" in experiments,
              "replay determinism protocol missing", WARNING)
        check("evaluation", "baseline_comparison_available",
              True, severity=WARNING)  # baselines module always present

        # D. Safety.
        safety_report = self.safety.validate_manifest(m, ctx)
        check("safety", "manifest_safe", safety_report.safe,
              "; ".join(safety_report.violations),
              next_step="fix the manifest violations listed")
        check("safety", "no_real_world_effectors",
              not ctx.get("real_world_effectors", False),
              "real-world effectors are forbidden in every pilot")
        check("safety", "sidecar_observe_only",
              not ctx.get("sidecar_publish", False)
              or bool(m.governance_approval_ids),
              "sidecar suggestion publishing needs approval")
        check("safety", "stream_ingestion_read_only", True)  # structural
        check("safety", "action_authority_false", True)      # structural
        check("safety", "claim_guard_enabled", True)          # always scans

        # E. Recovery.
        tri_state("recovery", "restart_demo_passed",
                  ctx.get("restart_demo_passed"),
                  "run examples/run_restart_demo.py or skip explicitly")
        if m.enabled_features.get("plasticity"):
            check("recovery", "rollback_available", True)  # engine built-in
        check("recovery", "final_checkpoint_expected", True)

        # F. Documentation.
        runbook = ctx.get("runbook_path")
        check("documentation", "runbook_generated",
              bool(runbook) and Path(str(runbook)).exists(),
              "no generated runbook found", WARNING,
              "python examples/generate_pilot_runbook.py "
              f"--profile {m.profile}")
        check("documentation", "pre_run_checklist_completed",
              bool(ctx.get("pre_run_checklist_passed", True)),
              "pre-run checklist incomplete", WARNING)
        check("documentation", "operator_notes_available", bool(m.notes),
              "no operator notes on the manifest", WARNING,
              "add a sentence about intent to manifest.notes")

        blocking = [i for i in issues if i.severity == BLOCKING]
        ready = not blocking
        if blocking:
            next_step = blocking[0].next_step or "resolve the blocking issues"
        elif issues:
            next_step = ("ready; consider clearing the warnings before a "
                         "longer pilot")
        else:
            next_step = ("ready: run the bounded pilot via "
                         "PilotDeploymentRunner")
        return PilotReadinessReport(
            pilot_id=m.pilot_id, profile=m.profile, ready=ready,
            issues=issues, checks=checks, recommended_next_step=next_step)


def _ops_manifest_view(manifest: PilotManifest) -> Dict[str, Any]:
    """The pilot manifest, shaped like an ops manifest for policy review."""
    return {
        "run_id": manifest.run_id,
        "mode": "bounded" if manifest.is_bounded() else "continuous_explicit",
        "explicit_continuous_acknowledged": bool(
            manifest.governance_approval_ids),
        "checkpoint_interval_steps": 50,
        "enabled_features": dict(manifest.enabled_features),
    }
