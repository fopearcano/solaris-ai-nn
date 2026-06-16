"""Alpha demo plan -- the bounded fixture path from input to alpha report.

:class:`AlphaDemoPlan` lays out the bounded end-to-end fixture steps. Every step is
bounded; a missing optional module produces a skipped/warning status (never a fake
success); a missing required foundation blocks the demo. No step starts feeders,
touches the network/Git/GitHub/shell/OS/hardware, or claims consciousness/life/
agency. The plan describes steps; the orchestrator executes the bounded, local
parts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AlphaDemoStepStatus:
    PENDING = "pending"
    COMPLETED = "completed"
    COMPLETED_FALLBACK = "completed_fallback"
    SKIPPED = "skipped"
    WARNING = "warning"
    BLOCKED = "blocked"

    ALL = (PENDING, COMPLETED, COMPLETED_FALLBACK, SKIPPED, WARNING, BLOCKED)


# (step id, label, module key or "" for foundation, required)
_STEPS = (
    ("init_state", "initialize alpha state", "", True),
    ("load_fixture", "load or create fixture sensory stream", "", True),
    ("sensorium_pass", "run minimal sensorium/organism fixture pass",
     "organismic_demo", False),
    ("metabolism_pass", "run perceptual metabolism fixture pass",
     "perceptual_metabolism", False),
    ("ontogenesis_pass", "run ontogenesis fixture pass",
     "perceptual_ontogenesis", False),
    ("semiogenesis_pass", "run semiogenesis fixture pass", "semiogenesis", False),
    ("cognition_pass", "run cognition fixture pass", "sensorium_cognition",
     False),
    ("self_boundary_pass", "run self-boundary fixture pass", "self_boundary",
     False),
    ("desire_action_pass", "run desire/action-reaction fixture pass",
     "action_reaction", False),
    ("developmental_pass", "run developmental-life short pass",
     "developmental_life", False),
    ("evidence_summary", "generate local evidence summary", "", True),
    ("claim_summary", "generate scientific claim summary", "scientific_claims",
     False),
    ("review_pack", "generate independent review mini-pack",
     "independent_review", False),
    ("cycle_status", "generate research cycle status", "research_cycle", False),
    ("alpha_report", "generate alpha report", "", True),
)


@dataclass
class AlphaDemoStep:
    """One bounded demo step."""

    step_id: str
    label: str
    module_key: str = ""
    required: bool = False
    status: str = AlphaDemoStepStatus.PENDING
    artifact_ref: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in AlphaDemoStepStatus.ALL:
            self.status = AlphaDemoStepStatus.PENDING

    @property
    def completed(self) -> bool:
        return self.status in (AlphaDemoStepStatus.COMPLETED,
                               AlphaDemoStepStatus.COMPLETED_FALLBACK)

    @property
    def skipped(self) -> bool:
        return self.status in (AlphaDemoStepStatus.SKIPPED,
                               AlphaDemoStepStatus.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        return {"step_id": self.step_id, "label": self.label,
                "module_key": self.module_key, "required": self.required,
                "status": self.status, "artifact_ref": self.artifact_ref,
                "detail": self.detail, "completed": self.completed,
                "skipped": self.skipped, "executes_external": False}


@dataclass
class AlphaDemoPlan:
    """The bounded end-to-end fixture demo plan."""

    steps: List[AlphaDemoStep] = field(default_factory=list)

    @classmethod
    def build(cls) -> "AlphaDemoPlan":
        plan = cls()
        for step_id, label, module_key, required in _STEPS:
            plan.steps.append(AlphaDemoStep(
                step_id=step_id, label=label, module_key=module_key,
                required=required))
        return plan

    def get(self, step_id: str) -> Optional[AlphaDemoStep]:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def summary(self) -> Dict[str, Any]:
        return {
            "alpha_demo_step_count": len(self.steps),
            "alpha_demo_step_completed_count": sum(1 for s in self.steps
                                                   if s.completed),
            "alpha_demo_step_skipped_count": sum(1 for s in self.steps
                                                 if s.skipped),
            "alpha_demo_step_blocked_count": sum(
                1 for s in self.steps
                if s.status == AlphaDemoStepStatus.BLOCKED),
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.summary()
        d["steps"] = [s.to_dict() for s in self.steps]
        d["note"] = ("every step is bounded; missing optional modules are "
                     "skipped honestly (never faked); no step starts feeders, "
                     "touches network/Git/GitHub/shell/OS/hardware, or claims "
                     "consciousness/life/agency")
        return d
