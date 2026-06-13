"""Tests for sampling actions and scopes."""

from __future__ import annotations

import pytest

from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionResult,
    SamplingActionType,
    SamplingScope,
    no_sampling_action,
)


def test_sixteen_action_types():
    assert len(SamplingActionType.ALL) == 16


def test_five_scopes():
    assert len(SamplingScope.ALL) == 5
    assert SamplingScope.FORBIDDEN in SamplingScope.ALL
    assert SamplingScope.FORBIDDEN not in SamplingScope.RUNNABLE


def test_action_serializes_and_clamps():
    action = SamplingAction(
        action_type=SamplingActionType.LOOK,
        scope=SamplingScope.SIMULATION_ONLY,
        expected_information_gain=5.0, confidence=2.0)
    data = action.to_dict()
    assert data["action_type"] == "look"
    assert action.expected_information_gain == 1.0  # clamped
    assert action.confidence == 1.0
    assert action.action_id.startswith("SMP_")


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        SamplingAction(action_type="teleport")


def test_unknown_scope_rejected():
    with pytest.raises(ValueError):
        SamplingAction(action_type=SamplingActionType.LOOK, scope="real")


def test_no_real_world_authority_structural():
    action = SamplingAction(action_type=SamplingActionType.OBSERVE_SIDECAR_ONLY,
                            scope=SamplingScope.SIDECAR_OBSERVE_ONLY)
    assert action.can_publish_suggestions() is False
    assert action.can_modify_input_stream() is False
    assert action.is_observe_only is True


def test_no_sampling_action_is_safe():
    action = no_sampling_action("nothing to do")
    assert action.action_type == "no_sampling_action"
    assert action.scope == SamplingScope.INTERNAL_ONLY
    assert action.safety_status == "ok"


def test_result_serializes():
    result = SamplingActionResult(
        action_id="SMP_x", action_type="look",
        scope=SamplingScope.SIMULATION_ONLY, executed=True)
    assert result.to_dict()["executed"] is True


def test_to_action_candidate_is_suggestion():
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.SIMULATION_ONLY)
    candidate = action.to_action_candidate()
    assert candidate.committed is False
    assert candidate.label == "look"
    assert candidate.executable_scope == "simulation_only"


def test_internal_action_candidate_scope():
    action = SamplingAction(
        action_type=SamplingActionType.REPLAY_UNCERTAIN_TRACE,
        scope=SamplingScope.INTERNAL_ONLY)
    candidate = action.to_action_candidate()
    assert candidate.executable_scope == "internal_only"
