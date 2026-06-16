"""Post-merge validation plan: ordered, safety gates, no auto execution."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import build_post_merge_plan
from solaris_ai_nn.implementation_intake.post_merge_plan import PostMergeStageId


def test_stages_ordered():
    plan = build_post_merge_plan()
    ids = [s.stage_id for s in plan.stages]
    assert ids == list(PostMergeStageId.ORDER)
    assert [s.order for s in plan.stages] == list(range(1, len(plan.stages) + 1))


def test_safety_stages_block_later():
    plan = build_post_merge_plan()
    safety = [s for s in plan.stages if s.safety_critical]
    assert safety
    assert all(s.exit_criterion.blocks_later_stages_on_failure for s in safety)
    ids = [s.stage_id for s in plan.stages]
    assert ids.index(PostMergeStageId.RUN_SAFETY_INVARIANTS) < ids.index(
        PostMergeStageId.RUN_MINI_SOAK)


def test_no_automatic_execution():
    plan = build_post_merge_plan().to_dict()
    assert plan["auto_executed"] is False
    assert "not executed automatically" in build_post_merge_plan(
        ).render_markdown()


def test_conditional_when_blocked():
    plan = build_post_merge_plan(conditional=True)
    assert plan.conditional is True
    assert "Conditional" in plan.render_markdown()


def test_includes_soak_replication_falsification():
    ids = {s.stage_id for s in build_post_merge_plan().stages}
    assert PostMergeStageId.RUN_MINI_SOAK in ids
    assert PostMergeStageId.REGISTER_IN_REPLICATION in ids
    assert PostMergeStageId.RUN_FALSIFICATION_REPLAY in ids
