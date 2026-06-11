"""Tests for the action arbitrator."""

from __future__ import annotations

from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
    no_action_candidate,
)
from solaris_ai_nn.executive.arbitration import (
    SCORE_COMPONENTS,
    ActionArbitrator,
)


def _candidate(label, utility=0.5, inhibited=False, safety="ok"):
    return ActionCandidate(
        action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
        label=label, utility_estimate=utility, confidence=0.6,
        executable_scope=ExecutableScope.SIMULATION_ONLY,
        inhibited=inhibited, safety_status=safety)


def test_safe_lower_utility_beats_unsafe_high_utility():
    arbitrator = ActionArbitrator()
    safe_low = _candidate("rest", utility=0.2)
    unsafe_high = _candidate("explore_safely", utility=0.95,
                             safety="rejected")
    result = arbitrator.select([safe_low, unsafe_high,
                                no_action_candidate()], {})
    assert result.selected.label == "rest"
    blocked = [s for s in result.scores
               if s.candidate.label == "explore_safely"][0]
    assert blocked.blocked
    assert blocked.total < -5  # the penalty dominates everything


def test_score_components_visible():
    arbitrator = ActionArbitrator()
    score = arbitrator.score_candidate(_candidate("rest"), {
        "drive_priorities": {"energy_drive": 0.7},
        "world_model_support": {"rest": 0.5},
        "habit_support": {"rest": 0.3},
        "mysterium_pressure": 0.4})
    assert set(score.components) == set(SCORE_COMPONENTS)
    assert len(SCORE_COMPONENTS) == 14
    data = score.to_dict()
    assert "components" in data and "total" in data


def test_no_safe_candidates_falls_back():
    arbitrator = ActionArbitrator()
    all_blocked = [_candidate("look", inhibited=True),
                   _candidate("rest", safety="rejected")]
    result = arbitrator.select(all_blocked, {})
    assert result.fallback_used
    assert result.selected.label == "no_action"
    # With a live operator-review candidate, that wins the fallback.
    review = ActionCandidate(
        action_type=ActionCandidateType.OPERATOR_REVIEW_REQUEST,
        label="request_operator_review",
        executable_scope=ExecutableScope.NONE, safety_status="rejected")
    review.safety_status = "ok"
    review.inhibited = False
    blocked_no_action = no_action_candidate()
    blocked_no_action.inhibited = True
    result = arbitrator.select([_candidate("look", inhibited=True),
                                review, blocked_no_action], {})
    # review is viable so it wins outright (not even a fallback).
    assert result.selected.label == "request_operator_review"


def test_critical_health_blocks_embodied_candidates():
    arbitrator = ActionArbitrator()
    result = arbitrator.select([_candidate("look", utility=0.9),
                                no_action_candidate()],
                               {"health_level": "critical"})
    assert result.selected.label == "no_action"


def test_ranking_deterministic_and_reasoned():
    arbitrator = ActionArbitrator()
    candidates = [_candidate("rest", 0.4), _candidate("look", 0.4)]
    first = arbitrator.rank_candidates(candidates, {})
    second = arbitrator.rank_candidates(candidates, {})
    assert [s.candidate.label for s in first] \
        == [s.candidate.label for s in second]
    result = arbitrator.select(candidates, {})
    assert "dominant component" in result.reason
    snap = arbitrator.snapshot()
    assert snap["selections_total"] == 1
