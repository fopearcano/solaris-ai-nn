"""Pilot-4 future approval workflow -- a checklist, never an approval.

The :class:`FutureApprovalWorkflow` is a specification of the steps a future
external action would have to pass. It is not executable approval: it cannot
approve a real action in the current code. It is a checklist, never a grant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ApprovalRequirement:
    """One prerequisite a future approval step would depend on."""

    name: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ApprovalStep:
    """One step in the future approval checklist (never executed)."""

    name: str
    description: str
    satisfied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_STEPS = (
    ("preflight_success", "the embodiment preflight passes"),
    ("risk_assessment", "a completed external-actuation risk assessment"),
    ("consent_record", "an explicit consent record"),
    ("safety_case", "an accepted safety case"),
    ("operator_approval", "explicit operator approval"),
    ("dry_run_replay", "a clean dry-run replay"),
    ("sandbox_replay", "a clean sandbox replay"),
    ("firewall_audit", "a passing firewall audit"),
    ("emergency_stop_test", "a successful emergency-stop test"),
    ("independent_review", "an independent safety review"),
    ("limited_single_action_pilot", "a limited, single-action pilot"),
)


@dataclass
class FutureApprovalWorkflow:
    """Holds the future approval checklist; cannot approve real action."""

    steps: List[ApprovalStep] = field(default_factory=list)
    is_executable_approval: bool = False
    can_approve_real_action: bool = False

    def __post_init__(self) -> None:
        if not self.steps:
            self.steps = [ApprovalStep(n, d) for n, d in _STEPS]
        # Invariants: this is a checklist, never executable approval.
        self.is_executable_approval = False
        self.can_approve_real_action = False

    def mark(self, step_name: str, satisfied: bool = True) -> None:
        """Mark a checklist step as (planning-time) satisfied; not approval."""
        for step in self.steps:
            if step.name == step_name:
                step.satisfied = bool(satisfied)
                return
        raise ValueError(f"unknown approval step {step_name!r}")

    def approve(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Approval is never executable in Pilot-4; this always refuses."""
        return {"approved": False,
                "reason": "Pilot-4 is planning-only; this checklist cannot "
                          "approve a real action",
                "real_world_actuation_enabled": False}

    @property
    def completeness(self) -> float:
        if not self.steps:
            return 0.0
        return round(sum(1 for s in self.steps if s.satisfied)
                     / len(self.steps), 4)

    def step_names(self) -> List[str]:
        return [s.name for s in self.steps]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "step_count": len(self.steps),
            "steps": self.step_names(),
            "completeness": self.completeness,
            "is_executable_approval": False,
            "can_approve_real_action": False,
            "note": "checklist/specification only; cannot approve real action",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": [s.to_dict() for s in self.steps],
                "is_executable_approval": False,
                "can_approve_real_action": False}
