"""Experiment rollback plan -- documented instructions, never executed.

:class:`ExperimentRollbackPlan` documents the triggers and steps to undo an
implementation if it goes wrong. It is *instructions only*: it never executes a
rollback, and every step preserves the failed artifacts as evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class RollbackTrigger:
    SAFETY_GATE_FAILURE = "safety_gate_failure"
    TEST_FAILURE = "test_failure"
    CLAIM_GUARD_FAILURE = "claim_guard_failure"
    FALSIFICATION_FAILURE = "falsification_failure"
    REGRESSION_INCREASE = "regression_increase"
    CONTAMINATION_INCREASE = "contamination_increase"
    FIXTURE_OVERFIT_INCREASE = "fixture_overfit_increase"
    SOURCE_BOUNDARY_VIOLATION = "source_boundary_violation"
    NO_MEASURABLE_EFFECT = "no_measurable_effect"
    RESOURCE_BLOWUP = "resource_blowup"
    OPERATOR_REJECTION = "operator_rejection"

    ALL = (SAFETY_GATE_FAILURE, TEST_FAILURE, CLAIM_GUARD_FAILURE,
           FALSIFICATION_FAILURE, REGRESSION_INCREASE, CONTAMINATION_INCREASE,
           FIXTURE_OVERFIT_INCREASE, SOURCE_BOUNDARY_VIOLATION,
           NO_MEASURABLE_EFFECT, RESOURCE_BLOWUP, OPERATOR_REJECTION)


@dataclass
class RollbackStep:
    """One documented rollback step (instruction only)."""

    order: int
    instruction: str
    preserves_evidence: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"order": self.order, "instruction": self.instruction,
                "preserves_evidence": self.preserves_evidence}


@dataclass
class ExperimentRollbackPlan:
    """Documented rollback triggers + steps (never executed automatically)."""

    spec_id: str
    triggers: List[str] = field(default_factory=list)
    steps: List[RollbackStep] = field(default_factory=list)

    def render_markdown(self) -> str:
        lines = [f"# Rollback Plan -- {self.spec_id}", "",
                 "## Triggers (any of)", ""]
        lines += [f"- {t}" for t in self.triggers]
        lines += ["", "## Steps (manual, evidence-preserving)", ""]
        lines += [f"{s.order}. {s.instruction}" for s in self.steps]
        lines += ["", "_This is a documented plan. It is never executed "
                  "automatically, and every step preserves the failed "
                  "artifacts as evidence._"]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {"spec_id": self.spec_id, "triggers": list(self.triggers),
                "steps": [s.to_dict() for s in self.steps],
                "executed": False, "preserves_evidence": True}


def build_rollback_plan(spec: Dict[str, Any]) -> ExperimentRollbackPlan:
    steps = [
        RollbackStep(1, "stop and record the triggering failure as evidence"),
        RollbackStep(2, "do NOT delete the failed branch artifacts or reports"),
        RollbackStep(3, "revert the working tree to the pre-experiment commit "
                        "(manual `git revert`/`git restore` by the operator)"),
        RollbackStep(4, "archive the spec and attach the failure evidence"),
        RollbackStep(5, "register the failure for cross-run replication so it "
                        "is not silently repeated")]
    return ExperimentRollbackPlan(spec_id=spec.get("spec_id", "spec"),
                                  triggers=list(RollbackTrigger.ALL),
                                  steps=steps)
