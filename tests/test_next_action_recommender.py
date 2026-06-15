"""NextActionRecommender: safety first; baseline; review; never real actuation."""

from __future__ import annotations

from solaris_ai_nn.operator_console import (
    NextActionPriority,
    NextActionRecommender,
    NextActionType,
)


def test_critical_safety_blocker_prioritized():
    top = NextActionRecommender().top(
        safety_status={"critical_failure": True})
    assert top.action_type == NextActionType.RUN_SAFETY_FULL_CHECK
    assert top.priority == NextActionPriority.IMMEDIATE


def test_missing_safety_state_runs_fast_check():
    top = NextActionRecommender().top(safety_status=None)
    assert top.action_type == NextActionType.RUN_SAFETY_FAST_CHECK


def test_missing_evidence_recommends_baseline():
    top = NextActionRecommender().top(safety_status={"status": "ok"})
    assert top.action_type == NextActionType.RUN_RESEARCH_BASELINE


def test_architecture_evidence_recommends_review():
    top = NextActionRecommender().top(
        safety_status={"status": "ok"},
        research_findings={"baseline_done": True})
    assert top.action_type == NextActionType.RUN_ARCHITECTURE_REVIEW


def test_never_recommends_real_actuation():
    recs = NextActionRecommender().recommend(
        safety_status={"status": "ok"},
        research_findings={"x": 1},
        architecture_roadmap={"items": 5})
    types = {r.action_type for r in recs}
    assert types <= set(NextActionType.ALL)
    assert all("actuat" not in t and "real_world" not in t for t in types)
    assert all("disable" not in t for t in types)
