"""Post-implementation validation plan -- staged, gated, never auto-executed.

:class:`PostImplementationValidationPlan` lays out the staged validation an
implementation must pass (static inspection -> unit -> integration -> safety ->
example runs -> short developmental demo -> mini soak -> ablation comparison ->
falsification replay -> replication registration). Later stages require earlier
stages to pass, a safety failure blocks continuation, and the plan never executes
automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class ValidationStageId:
    STATIC_INSPECTION = "static_inspection"
    UNIT_TESTS = "unit_tests"
    INTEGRATION_TESTS = "integration_tests"
    SAFETY_TESTS = "safety_tests"
    EXAMPLE_RUNS = "example_runs"
    SHORT_DEVELOPMENTAL_DEMO = "short_developmental_demo"
    MINI_SOAK = "mini_soak"
    ABLATION_COMPARISON = "ablation_comparison"
    FALSIFICATION_REPLAY = "falsification_replay"
    REPLICATION_REGISTRATION = "replication_registration"

    ORDER = (STATIC_INSPECTION, UNIT_TESTS, INTEGRATION_TESTS, SAFETY_TESTS,
             EXAMPLE_RUNS, SHORT_DEVELOPMENTAL_DEMO, MINI_SOAK,
             ABLATION_COMPARISON, FALSIFICATION_REPLAY,
             REPLICATION_REGISTRATION)


@dataclass
class ValidationExitCriteria:
    """The exit criteria + blocking semantics for one stage."""

    must_pass: List[str] = field(default_factory=list)
    blocks_continuation_on_failure: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"must_pass": list(self.must_pass),
                "blocks_continuation_on_failure":
                    self.blocks_continuation_on_failure}


@dataclass
class ValidationStage:
    """One staged validation step (must follow earlier stages)."""

    order: int
    stage_id: str
    purpose: str
    exit_criteria: ValidationExitCriteria
    safety_critical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"order": self.order, "stage_id": self.stage_id,
                "purpose": self.purpose,
                "exit_criteria": self.exit_criteria.to_dict(),
                "safety_critical": self.safety_critical}


@dataclass
class PostImplementationValidationPlan:
    """The ordered, gated validation plan (never auto-executed)."""

    spec_id: str
    stages: List[ValidationStage] = field(default_factory=list)

    def render_markdown(self) -> str:
        lines = [f"# Validation Plan -- {self.spec_id}", "",
                 "_Staged and gated. Later stages require earlier stages to "
                 "pass; a safety failure blocks continuation. This plan is not "
                 "executed automatically._", ""]
        for s in self.stages:
            flag = " (safety-critical)" if s.safety_critical else ""
            lines.append(f"{s.order}. **{s.stage_id}**{flag} -- {s.purpose}")
            for c in s.exit_criteria.must_pass:
                lines.append(f"   - exit: {c}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {"spec_id": self.spec_id,
                "stage_count": len(self.stages),
                "stages": [s.to_dict() for s in self.stages],
                "auto_executed": False}


_PURPOSE = {
    ValidationStageId.STATIC_INSPECTION: "inspect the diff; no unrelated files",
    ValidationStageId.UNIT_TESTS: "the new behavior is correct",
    ValidationStageId.INTEGRATION_TESTS: "integration with the stack holds",
    ValidationStageId.SAFETY_TESTS: "all safety boundaries hold",
    ValidationStageId.EXAMPLE_RUNS: "the bounded example runs (exit 0)",
    ValidationStageId.SHORT_DEVELOPMENTAL_DEMO: "a short developmental demo runs",
    ValidationStageId.MINI_SOAK: "a mini bounded soak runs and is preserved",
    ValidationStageId.ABLATION_COMPARISON: "compare against the control arm",
    ValidationStageId.FALSIFICATION_REPLAY: "replay the falsification probes",
    ValidationStageId.REPLICATION_REGISTRATION: "register the run for replication",
}


def build_validation_plan(spec: Dict[str, Any],
                          ) -> PostImplementationValidationPlan:
    stages: List[ValidationStage] = []
    for i, sid in enumerate(ValidationStageId.ORDER):
        safety = sid == ValidationStageId.SAFETY_TESTS
        stages.append(ValidationStage(
            order=i + 1, stage_id=sid, purpose=_PURPOSE[sid],
            safety_critical=safety,
            exit_criteria=ValidationExitCriteria(
                must_pass=[_PURPOSE[sid]],
                blocks_continuation_on_failure=True)))
    return PostImplementationValidationPlan(
        spec_id=spec.get("spec_id", "spec"), stages=stages)
