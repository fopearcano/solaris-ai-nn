"""Next action planner: operator instructions; never executed; blocker first."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import (
    NextActionPriority,
    NextActionType,
    NextActionPlanner,
    ResearchCycleStage,
)


def test_stage_action_for_validated_baseline():
    actions = NextActionPlanner().plan(
        stage=ResearchCycleStage.RESEARCH_BASELINE_VALIDATED, blocked=False)
    assert actions[0].action_type == NextActionType.RUN_MINI_SOAK


def test_high_risk_action_carries_safety_context():
    actions = NextActionPlanner().plan(
        stage=ResearchCycleStage.EXPERIMENT_PACK_COMPILED, blocked=False)
    assert actions[0].action_type == \
        NextActionType.GIVE_PROMPT_TO_EXTERNAL_AGENT
    assert actions[0].safety_context


def test_blocked_action_is_resolve_blocker():
    actions = NextActionPlanner().plan(
        stage=ResearchCycleStage.BLOCKED, blocked=True, blocked_states=[
            {"reason": "safety_gate_failed", "critical_safety": True,
             "recommendation": "run_safety_audit"}])
    assert actions[0].action_type == NextActionType.RESOLVE_BLOCKER
    assert actions[0].priority == NextActionPriority.URGENT
    assert "cannot be bypassed" in actions[0].safety_context


def test_actions_never_executed():
    summary = NextActionPlanner.summary(NextActionPlanner().plan(
        stage=ResearchCycleStage.CYCLE_COMPLETE, blocked=False))
    assert summary["executes_automatically"] is False
    assert all(a["executed"] is False and a["for_operator"] is True
               for a in summary["actions"])
