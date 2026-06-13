"""Tests for active perception safety hard rules."""

from __future__ import annotations

from solaris_ai_nn.active_perception.safety import (
    HARD_RULES,
    MAX_ACTIONS_PER_STEP,
    MAX_REPEAT_BEFORE_LOOP,
    ActivePerceptionSafetyValidator,
)
from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingPressure,
    SamplingScope,
)


def test_ten_hard_rules():
    assert len(HARD_RULES) == 10


def test_structural_negatives():
    v = ActivePerceptionSafetyValidator()
    assert v.sampling_can_act_in_real_world() is False
    assert v.sampling_can_network() is False
    assert v.sampling_can_commit_sidecar() is False


def test_blocks_real_world_action():
    v = ActivePerceptionSafetyValidator()
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.SIMULATION_ONLY,
                            target_ref="https://example.com/api")
    assert not v.validate_action(action).safe


def test_blocks_stream_modification():
    v = ActivePerceptionSafetyValidator()
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.READ_ONLY_STREAM)
    assert not v.validate_action(action, {"modifies_stream": True}).safe


def test_blocks_sidecar_commit():
    v = ActivePerceptionSafetyValidator()
    action = SamplingAction(
        action_type=SamplingActionType.OBSERVE_SIDECAR_ONLY,
        scope=SamplingScope.SIDECAR_OBSERVE_ONLY)
    assert not v.validate_action(action, {"commit": True}).safe


def test_blocks_unbounded_batch():
    v = ActivePerceptionSafetyValidator()
    actions = [SamplingAction(action_type=SamplingActionType.LOOK,
                              scope=SamplingScope.SIMULATION_ONLY)
               for _ in range(MAX_ACTIONS_PER_STEP + 2)]
    assert not v.validate_batch(actions).safe


def test_blocks_loop():
    v = ActivePerceptionSafetyValidator()
    assert not v.validate_loop(MAX_REPEAT_BEFORE_LOOP + 1).safe


def test_curiosity_cannot_override_safety():
    v = ActivePerceptionSafetyValidator()
    action = SamplingAction(action_type=SamplingActionType.SEEK_NOVELTY,
                            scope=SamplingScope.SIMULATION_ONLY,
                            source_pressure=SamplingPressure.MYSTERIUM)
    assert not v.validate_action(action, {"emergency": True}).safe


def test_pilot_stream_not_a_command():
    v = ActivePerceptionSafetyValidator()
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.READ_ONLY_STREAM)
    assert not v.validate_action(
        action, {"treat_stream_as_command": True}).safe


def test_clean_action_passes():
    v = ActivePerceptionSafetyValidator()
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.SIMULATION_ONLY)
    assert v.validate_action(action, {"health_level": "ok"}).safe


def test_report_claim_guard():
    v = ActivePerceptionSafetyValidator()
    assert v.validate_report_text("The system sampled 3 targets.").safe
