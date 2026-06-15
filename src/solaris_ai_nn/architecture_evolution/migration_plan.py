"""Migration plans -- a checklist for a human, executed by no one here.

A :class:`MigrationPlan` lists the preconditions, likely-affected files, tests to
run, docs to update, state-migration needs, compatibility risks, rollback steps,
and a safety-invariant checklist for a proposed change, plus an operator-signoff
field. It is planning only: no code is edited and no migration is executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class MigrationStatus:
    PLANNED = "planned"
    AWAITING_OPERATOR_SIGNOFF = "awaiting_operator_signoff"
    NOT_EXECUTED = "not_executed"

    ALL = (PLANNED, AWAITING_OPERATOR_SIGNOFF, NOT_EXECUTED)


class MigrationRisk:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"

    ALL = (LOW, MODERATE, HIGH, UNKNOWN)


@dataclass
class MigrationStep:
    order: int
    description: str
    manual: bool = True  # every step is performed manually by a human

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class MigrationPlan:
    """A planning-only migration checklist; nothing is executed."""

    target_change: str
    preconditions: List[str] = field(default_factory=list)
    files_likely_affected: List[str] = field(default_factory=list)
    tests_to_run: List[str] = field(default_factory=list)
    docs_to_update: List[str] = field(default_factory=list)
    state_migration_needed: bool = False
    compatibility_risk: str = MigrationRisk.UNKNOWN
    steps: List[MigrationStep] = field(default_factory=list)
    rollback_steps: List[str] = field(default_factory=list)
    validation_checklist: List[str] = field(default_factory=list)
    safety_invariant_checklist: List[str] = field(default_factory=list)
    operator_signoff: Optional[str] = None
    status: str = MigrationStatus.NOT_EXECUTED

    def __post_init__(self) -> None:
        if not self.validation_checklist:
            self.validation_checklist = [
                "run `python -m pytest`",
                "run the affected examples",
                "confirm metrics remain comparable or note the break",
            ]
        if not self.safety_invariant_checklist:
            self.safety_invariant_checklist = [
                "run the fast safety invariant check before and after",
                "confirm no safety-critical module was removed",
                "confirm real_world_actuation remains disabled",
            ]
        if not self.rollback_steps:
            self.rollback_steps = ["revert the manual change",
                                   "restore the prior module registry entry"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_change": self.target_change,
            "preconditions": self.preconditions,
            "files_likely_affected": self.files_likely_affected,
            "tests_to_run": self.tests_to_run,
            "docs_to_update": self.docs_to_update,
            "state_migration_needed": self.state_migration_needed,
            "compatibility_risk": self.compatibility_risk,
            "steps": [s.to_dict() for s in self.steps],
            "rollback_steps": self.rollback_steps,
            "validation_checklist": self.validation_checklist,
            "safety_invariant_checklist": self.safety_invariant_checklist,
            "operator_signoff": self.operator_signoff,
            "status": self.status,
            "note": "planning only; no code is edited and no migration is "
                    "executed",
        }


def build_migration_plan(target_change: str, affected_modules: List[str], *,
                         touches_state: bool = False,
                         compatibility_risk: str = MigrationRisk.MODERATE,
                         ) -> MigrationPlan:
    steps = [
        MigrationStep(1, "open an ADR and obtain operator approval"),
        MigrationStep(2, "make the change manually in a branch"),
        MigrationStep(3, "update the module registry / scenario profiles"),
        MigrationStep(4, "run tests and the affected examples"),
        MigrationStep(5, "run the safety invariant checks"),
    ]
    return MigrationPlan(
        target_change=target_change,
        preconditions=["an approved ADR exists",
                       "safety invariants are passing"],
        files_likely_affected=[f"src/solaris_ai_nn/{m}/" for m in
                               affected_modules],
        tests_to_run=[f"tests touching {m}" for m in affected_modules],
        docs_to_update=["docs/ARCHITECTURE.md", "README.md"],
        state_migration_needed=touches_state,
        compatibility_risk=compatibility_risk, steps=steps,
        status=MigrationStatus.AWAITING_OPERATOR_SIGNOFF)
