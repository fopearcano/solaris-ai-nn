"""Tests for action candidates."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateSet,
    ActionCandidateType,
    ExecutableScope,
    candidate_from_desire,
    no_action_candidate,
)
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def test_candidate_serializes():
    candidate = ActionCandidate(
        action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
        label="rest", expected_effect="restore energy",
        executable_scope=ExecutableScope.SIMULATION_ONLY)
    data = candidate.to_dict()
    json.dumps(data)
    for key in ("action_id", "action_type", "label", "source_desire_id",
                "expected_effect", "expected_cost", "expected_risk",
                "confidence", "utility_estimate", "safety_status",
                "governance_status", "executable_scope", "committed",
                "metadata"):
        assert key in data, key


def test_real_world_authority_absent():
    # committed=True is rejected at construction.
    with pytest.raises(ValueError):
        ActionCandidate(
            action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
            label="rest", committed=True,
            executable_scope=ExecutableScope.SIMULATION_ONLY)
    # Scopes are a closed set; there is no real-world scope at all.
    assert "real_world" not in ExecutableScope.ALL
    with pytest.raises(ValueError):
        ActionCandidate(action_type=ActionCandidateType.NO_ACTION,
                        label="x", executable_scope="real_world")


def test_no_action_candidate_valid():
    candidate = no_action_candidate("nothing demands action")
    assert candidate.action_type == ActionCandidateType.NO_ACTION
    assert candidate.executable_scope == ExecutableScope.NONE
    assert candidate.committed is False
    # The set always carries one.
    bundle = ActionCandidateSet(candidates=[])
    assert bundle.by_label("no_action") is not None


def test_sidecar_scope_enforced():
    with pytest.raises(ValueError):
        ActionCandidate(action_type=ActionCandidateType.SIDECAR_SUGGESTION,
                        label="suggest",
                        executable_scope=ExecutableScope.SIMULATION_ONLY)


def test_candidate_from_desire_maps_scope():
    rest = candidate_from_desire(DesireCandidate(proposal="rest",
                                                 motivation=0.7,
                                                 confidence=0.6))
    assert rest.executable_scope == ExecutableScope.SIMULATION_ONLY
    assert rest.expected_cost == 0.0  # resting is free
    review = candidate_from_desire(DesireCandidate(
        proposal="request_operator_review", motivation=0.9))
    assert review.action_type == ActionCandidateType.OPERATOR_REVIEW_REQUEST
    assert review.executable_scope == ExecutableScope.NONE
    blocked = candidate_from_desire(DesireCandidate(
        proposal="approach_reward", blocked=True, blocked_reason="tired"))
    assert blocked.inhibited and blocked.inhibition_reason == "tired"
