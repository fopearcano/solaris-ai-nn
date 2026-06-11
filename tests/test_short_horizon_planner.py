"""Tests for the short-horizon planner."""

from __future__ import annotations

from solaris_ai_nn.executive.planner import (
    PLAN_TEMPLATES,
    ActionPlan,
    PlanStep,
    ShortHorizonPlanner,
)


def test_builds_max_length_3_plan():
    planner = ShortHorizonPlanner(max_plan_length=3)
    plan = planner.build_plan("explore_safely", {})
    assert 1 <= len(plan) <= 3
    assert [s.label for s in plan.steps] == ["look", "explore_safely",
                                             "rest"]
    assert not plan.rejected


def test_rejects_long_plan():
    planner = ShortHorizonPlanner()
    long_plan = ActionPlan(goal="wander", steps=[
        PlanStep(index=i, label="look") for i in range(1, 8)])
    report = planner.safety.validate_plan(long_plan, {})
    assert not report.safe
    assert "long-horizon autonomous planning is refused" \
        in report.violations[0]
    # Even with a generous request, the hard max is 5.
    report = planner.safety.validate_plan(long_plan,
                                          {"max_plan_length": 99})
    assert not report.safe


def test_plan_steps_marked_suggestions_only():
    planner = ShortHorizonPlanner()
    plan = planner.build_plan("rest", {})
    assert all(s.suggestion_only for s in plan.steps)
    data = plan.to_dict()
    assert "suggestions only" in data["note"]


def test_blocked_steps_exposed():
    planner = ShortHorizonPlanner()
    plan = planner.build_plan(
        "approach_reward",
        {"governance_blocks": {"approach_reward": "operator pause"}})
    blocked = plan.blocked_steps()
    assert blocked and blocked[0].label == "approach_reward"
    assert "operator pause" in blocked[0].blocked_reason
    assert [s.label for s in plan.live_steps()] == ["look"]


def test_fully_blocked_plan_rejected():
    planner = ShortHorizonPlanner()
    plan = planner.build_plan("look",
                              {"latent_mode": "dream"})
    assert plan.rejected
    assert "nothing safe to suggest" in plan.rejected_reason
    assert planner.plans_rejected == 1


def test_select_plan_uses_prospection():
    planner = ShortHorizonPlanner()
    context = {"world_model_valence": {"rest": 0.6, "look": 0.1,
                                       "avoid_danger": 0.4}}
    plans = [planner.build_plan(goal, context)
             for goal in ("rest", "avoid_danger", "checkpoint_now")]
    selected = planner.select_plan(plans, context)
    assert selected is not None
    assert selected.prospection is not None
    assert not selected.rejected


def test_templates_cover_spec_pairs():
    assert PLAN_TEMPLATES["rest"] == ["rest", "look"]
    assert PLAN_TEMPLATES["avoid_danger"] == ["avoid_danger", "rest"]
    assert PLAN_TEMPLATES["checkpoint_now"] == ["checkpoint_now",
                                                "consolidate_memory"]
    assert PLAN_TEMPLATES["seek_signal"] == ["seek_signal", "emit_ping"]
    assert PLAN_TEMPLATES["remain_observe_only"] == ["remain_observe_only",
                                                     "no_action"]
    assert PLAN_TEMPLATES["request_operator_review"] == [
        "request_operator_review", "no_action"]
