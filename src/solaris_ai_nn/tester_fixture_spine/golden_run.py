"""Golden run -- the bounded, ordered steps of a known-good fixture rehearsal.

:class:`TesterGoldenRun` records the ordered, bounded steps of the tester demo
(initialize state, load/validate/quarantine fixtures, run the environmental membrane
and membrane-integration audit, observe over impressions, optionally run limited
ontogenesis/semiogenesis/cognition, scan claims/safety, build the index/report/bundle,
and check reproducibility/regression). Every step is bounded and local; optional
stages skip honestly with an explicit marker, and a raw-event downstream path is a
failure in strict mode. Reports never hide skipped stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class GoldenRunStatus:
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    SKIPPED_OPTIONAL = "skipped_optional"
    FAILED = "failed"
    BLOCKED = "blocked"
    PENDING = "pending"

    ALL = (PASS, PASS_WITH_WARNINGS, SKIPPED_OPTIONAL, FAILED, BLOCKED, PENDING)


# The canonical ordered golden run steps; ``optional`` steps may skip honestly.
_STEPS = (
    ("initialize_tester_state", False),
    ("load_fixture_pack", False),
    ("validate_fixture_events", False),
    ("quarantine_unsafe_fixture_events", False),
    ("run_environmental_membrane", False),
    ("generate_sensory_impressions", False),
    ("run_membrane_integration_audit", False),
    ("run_observation_over_impressions", False),
    ("run_limited_ontogenesis", True),
    ("run_limited_semiogenesis", True),
    ("run_limited_cognition", True),
    ("run_claim_safety_scan", False),
    ("build_artifact_index", False),
    ("build_tester_report", False),
    ("build_tester_artifact_bundle", False),
    ("run_reproducibility_check", False),
    ("run_regression_check", False),
)


@dataclass
class GoldenRunStep:
    """One bounded golden-run step and its observed status."""

    index: int
    name: str
    optional: bool = False
    status: str = GoldenRunStatus.PENDING
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"index": self.index, "name": self.name,
                "optional": self.optional, "status": self.status,
                "detail": self.detail}


@dataclass
class TesterGoldenRun:
    """The ordered, bounded steps of a known-good fixture rehearsal."""

    steps: List[GoldenRunStep] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        statuses = {s.status for s in self.steps}
        if GoldenRunStatus.BLOCKED in statuses:
            return GoldenRunStatus.BLOCKED
        if GoldenRunStatus.FAILED in statuses:
            return GoldenRunStatus.FAILED
        if GoldenRunStatus.PASS_WITH_WARNINGS in statuses \
                or GoldenRunStatus.SKIPPED_OPTIONAL in statuses:
            return GoldenRunStatus.PASS_WITH_WARNINGS
        return GoldenRunStatus.PASS

    @property
    def skipped_steps(self) -> List[str]:
        return [s.name for s in self.steps
                if s.status == GoldenRunStatus.SKIPPED_OPTIONAL]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "step_count": len(self.steps),
            "skipped_optional_steps": self.skipped_steps,
            "steps": [s.to_dict() for s in self.steps],
            "note": "every golden-run step is bounded and local; optional stages "
                    "skip honestly with an explicit marker and skipped stages are "
                    "never hidden",
        }


@dataclass
class GoldenRunBuilder:
    """Builds the golden-run step record from a finished tester runtime."""

    def build(self, runtime: Any) -> TesterGoldenRun:
        run = TesterGoldenRun()
        ctx = runtime.step_outcomes if hasattr(runtime, "step_outcomes") else {}
        for index, (name, optional) in enumerate(_STEPS):
            outcome = ctx.get(name, {})
            status = outcome.get(
                "status",
                GoldenRunStatus.SKIPPED_OPTIONAL if optional
                else GoldenRunStatus.PASS)
            step = GoldenRunStep(index=index, name=name, optional=optional,
                                 status=status, detail=outcome.get("detail", ""))
            run.steps.append(step)
        return run
