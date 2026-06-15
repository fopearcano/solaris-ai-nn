"""Run planner -- describe a run before anyone runs it.

:class:`RunPlanner` turns a catalogued profile into a :class:`RunPlan`: the
preconditions, the safety and governance checks, the confirmations required, the
expected writes / reports / evidence, the expected duration, and a safe-shutdown
plan. Planning never runs the profile, and every plan states plainly that
external authority is ``False`` and classifies the run as inspect-only, dry-run,
simulated, read-only, sandbox-only, or prohibited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .profile_catalog import ProfileCatalog, ProfileCatalogEntry, ProfileSafetyClass

# Map a safety class to the operator-facing run kind label.
_RUN_KIND = {
    ProfileSafetyClass.INSPECT_ONLY: "inspect-only",
    ProfileSafetyClass.PLAN_ONLY: "plan-only",
    ProfileSafetyClass.BOUNDED_FIXTURE: "simulated",
    ProfileSafetyClass.BOUNDED_SIMULATION: "simulated",
    ProfileSafetyClass.READ_ONLY_ENVIRONMENTAL: "read-only",
    ProfileSafetyClass.DRY_RUN_MOTOR: "dry-run",
    ProfileSafetyClass.SANDBOX_MOTOR: "sandbox-only",
    ProfileSafetyClass.LONG_RUN_PLAN: "plan-only",
    ProfileSafetyClass.LONG_RUN_REQUIRES_GOVERNANCE: "prohibited",
    ProfileSafetyClass.PROHIBITED: "prohibited",
}


@dataclass
class RunPlanStep:
    order: int
    description: str
    kind: str = "step"  # precondition | safety | governance | confirm | run

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RunPlanValidation:
    valid: bool
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "reasons": list(self.reasons)}


@dataclass
class RunPlan:
    """A described, not executed, plan for one profile."""

    profile_id: str
    run_kind: str
    safety_class: str
    can_run_from_console: bool
    external_authority: bool = False
    profile_summary: str = ""
    preconditions: List[str] = field(default_factory=list)
    safety_checks: List[str] = field(default_factory=list)
    governance_checks: List[str] = field(default_factory=list)
    required_confirmations: List[str] = field(default_factory=list)
    expected_writes: List[str] = field(default_factory=list)
    expected_reports: List[str] = field(default_factory=list)
    expected_evidence: List[str] = field(default_factory=list)
    expected_duration: str = ""
    rollback_plan: List[RunPlanStep] = field(default_factory=list)
    steps: List[RunPlanStep] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    validation: Optional[RunPlanValidation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "run_kind": self.run_kind,
            "safety_class": self.safety_class,
            "can_run_from_console": self.can_run_from_console,
            "external_authority": False,
            "profile_summary": self.profile_summary,
            "preconditions": list(self.preconditions),
            "safety_checks": list(self.safety_checks),
            "governance_checks": list(self.governance_checks),
            "required_confirmations": list(self.required_confirmations),
            "expected_writes": list(self.expected_writes),
            "expected_reports": list(self.expected_reports),
            "expected_evidence": list(self.expected_evidence),
            "expected_duration": self.expected_duration,
            "rollback_plan": [s.to_dict() for s in self.rollback_plan],
            "steps": [s.to_dict() for s in self.steps],
            "limitations": list(self.limitations),
            "validation": self.validation.to_dict() if self.validation else None,
        }


@dataclass
class RunPlanner:
    """Builds run plans from the profile catalog; runs nothing."""

    catalog: ProfileCatalog = field(default_factory=ProfileCatalog)

    def plan(self, profile_id: str) -> RunPlan:
        entry = self.catalog.get(profile_id)
        if entry is None:
            return RunPlan(
                profile_id=profile_id, run_kind="unknown",
                safety_class="unknown", can_run_from_console=False,
                profile_summary=f"unknown profile {profile_id!r}",
                validation=RunPlanValidation(
                    valid=False,
                    reasons=[f"unknown profile {profile_id!r}; planning "
                             "refused"]))
        return self._plan_entry(entry)

    def _plan_entry(self, entry: ProfileCatalogEntry) -> RunPlan:
        run_kind = _RUN_KIND.get(entry.safety_class, "simulated")
        prohibited = entry.safety_class in (
            ProfileSafetyClass.PROHIBITED,
            ProfileSafetyClass.LONG_RUN_REQUIRES_GOVERNANCE)
        steps: List[RunPlanStep] = []
        order = 0

        def add(desc: str, kind: str) -> None:
            nonlocal order
            order += 1
            steps.append(RunPlanStep(order=order, description=desc, kind=kind))

        preconditions = [
            "console authority is local; external authority is false",
            f"profile {entry.profile_id!r} is known to the catalog",
        ]
        add("verify the profile is known and not prohibited", "precondition")

        safety_checks: List[str] = []
        if entry.requires_safety_fast_check:
            safety_checks.append("fast safety-invariant check must pass")
            add("run the fast safety-invariant check", "safety")
        if entry.requires_safety_full_check:
            safety_checks.append("full safety-invariant check must pass "
                                 "(pilot profile)")
            add("run the full safety-invariant check", "safety")

        governance_checks: List[str] = []
        if entry.requires_governance:
            governance_checks.append(
                "governance scopes: "
                + ", ".join(entry.metadata.get("governance_requirements", []))
                + " must be approved")
            add("verify the required governance scopes are approved",
                "governance")

        confirmations: List[str] = []
        if entry.requires_operator_confirmation:
            confirmations.append("explicit operator --confirm is required")
            add("obtain explicit operator confirmation", "confirm")

        if prohibited:
            add("REFUSE: this profile cannot run from the console", "run")
        else:
            add(f"launch {entry.profile_id!r} via the conscience orchestrator "
                f"(bounded, {run_kind})", "run")

        rollback = [
            RunPlanStep(order=1, description="the run is bounded; it stops at "
                        "its step/duration limit", kind="rollback"),
            RunPlanStep(order=2, description="emergency stop remains available "
                        "and is never disabled", kind="rollback"),
            RunPlanStep(order=3, description="artifacts are append-only; no "
                        "source code is changed, so no code rollback is needed",
                        kind="rollback"),
        ]

        valid = not prohibited and entry.can_run_from_console
        reasons = ([] if valid else
                   [f"profile {entry.profile_id!r} ({entry.safety_class}) "
                    "cannot be launched from the console"])

        return RunPlan(
            profile_id=entry.profile_id,
            run_kind=run_kind,
            safety_class=entry.safety_class,
            can_run_from_console=entry.can_run_from_console,
            external_authority=False,
            profile_summary=entry.title,
            preconditions=preconditions,
            safety_checks=safety_checks,
            governance_checks=governance_checks,
            required_confirmations=confirmations,
            expected_writes=(["state/artifact directories only"]
                             if entry.writes_state else
                             ["no state writes (plan-only)"]),
            expected_reports=(["scenario report JSON"] if entry.writes_artifacts
                              else []),
            expected_evidence=["scenario_runs.jsonl", "scenario report"],
            expected_duration=entry.expected_duration,
            rollback_plan=rollback,
            steps=steps,
            limitations=list(entry.limitations) + ["external authority: false"],
            validation=RunPlanValidation(valid=valid, reasons=reasons))
