"""Post-merge validation plan -- staged, gated, never auto-executed.

:class:`PostMergeValidationPlan` lays out the staged validation to run after a
merge (re-run full tests -> examples -> safety invariants -> ClaimGuard -> short
fixture demo -> mini soak -> replication registry -> falsification replay ->
update architecture evidence -> update experiment queue). A safety failure stops
later validation, and the plan never executes automatically. It may be produced
even when merge is blocked (then marked conditional).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PostMergeStageId:
    RERUN_FULL_TESTS = "rerun_full_tests"
    RUN_EXAMPLES = "run_examples"
    RUN_SAFETY_INVARIANTS = "run_safety_invariants"
    RUN_CLAIMGUARD = "run_claimguard"
    RUN_SHORT_FIXTURE_DEMO = "run_short_fixture_demo"
    RUN_MINI_SOAK = "run_mini_soak"
    REGISTER_IN_REPLICATION = "register_in_replication_registry"
    RUN_FALSIFICATION_REPLAY = "run_falsification_replay"
    UPDATE_ARCHITECTURE_EVIDENCE = "update_architecture_evidence"
    UPDATE_EXPERIMENT_QUEUE = "update_experiment_queue"

    ORDER = (RERUN_FULL_TESTS, RUN_EXAMPLES, RUN_SAFETY_INVARIANTS,
             RUN_CLAIMGUARD, RUN_SHORT_FIXTURE_DEMO, RUN_MINI_SOAK,
             REGISTER_IN_REPLICATION, RUN_FALSIFICATION_REPLAY,
             UPDATE_ARCHITECTURE_EVIDENCE, UPDATE_EXPERIMENT_QUEUE)


@dataclass
class PostMergeExitCriterion:
    """The exit criterion + blocking semantics for one stage."""

    must_pass: str
    blocks_later_stages_on_failure: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"must_pass": self.must_pass,
                "blocks_later_stages_on_failure":
                    self.blocks_later_stages_on_failure}


@dataclass
class PostMergeValidationStage:
    """One staged post-merge validation step."""

    order: int
    stage_id: str
    purpose: str
    exit_criterion: PostMergeExitCriterion
    safety_critical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"order": self.order, "stage_id": self.stage_id,
                "purpose": self.purpose,
                "exit_criterion": self.exit_criterion.to_dict(),
                "safety_critical": self.safety_critical}


@dataclass
class PostMergeValidationPlan:
    """The ordered, gated post-merge validation plan (never auto-executed)."""

    stages: List[PostMergeValidationStage] = field(default_factory=list)
    conditional: bool = False

    def render_markdown(self) -> str:
        lines = ["# Post-Merge Validation Plan", ""]
        if self.conditional:
            lines += ["_Conditional: merge is currently blocked; run this plan "
                      "only after the blockers are resolved._", ""]
        lines += ["_Staged and gated. A safety failure stops later validation. "
                  "This plan is not executed automatically._", ""]
        for s in self.stages:
            flag = " (safety-critical)" if s.safety_critical else ""
            lines.append(f"{s.order}. **{s.stage_id}**{flag} -- {s.purpose}")
            lines.append(f"   - exit: {s.exit_criterion.must_pass}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {"stage_count": len(self.stages),
                "stages": [s.to_dict() for s in self.stages],
                "conditional": self.conditional, "auto_executed": False}


_PURPOSE = {
    PostMergeStageId.RERUN_FULL_TESTS: "re-run the full test suite",
    PostMergeStageId.RUN_EXAMPLES: "run the bounded examples (exit 0)",
    PostMergeStageId.RUN_SAFETY_INVARIANTS: "run the safety invariants",
    PostMergeStageId.RUN_CLAIMGUARD: "ClaimGuard-scan generated reports",
    PostMergeStageId.RUN_SHORT_FIXTURE_DEMO: "run a short fixture demo",
    PostMergeStageId.RUN_MINI_SOAK: "run a mini bounded soak; preserve it",
    PostMergeStageId.REGISTER_IN_REPLICATION: "register the run for replication",
    PostMergeStageId.RUN_FALSIFICATION_REPLAY: "replay the falsification probes",
    PostMergeStageId.UPDATE_ARCHITECTURE_EVIDENCE:
        "feed results into architecture evidence",
    PostMergeStageId.UPDATE_EXPERIMENT_QUEUE: "update the experiment queue",
}
_SAFETY_STAGES = (PostMergeStageId.RUN_SAFETY_INVARIANTS,
                  PostMergeStageId.RUN_CLAIMGUARD)


def build_post_merge_plan(*, conditional: bool = False,
                          ) -> PostMergeValidationPlan:
    stages: List[PostMergeValidationStage] = []
    for i, sid in enumerate(PostMergeStageId.ORDER):
        safety = sid in _SAFETY_STAGES
        stages.append(PostMergeValidationStage(
            order=i + 1, stage_id=sid, purpose=_PURPOSE[sid],
            safety_critical=safety,
            exit_criterion=PostMergeExitCriterion(
                must_pass=_PURPOSE[sid],
                blocks_later_stages_on_failure=True)))
    return PostMergeValidationPlan(stages=stages, conditional=conditional)
