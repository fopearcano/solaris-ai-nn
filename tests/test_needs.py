"""Tests for the need estimator."""

from __future__ import annotations

import pytest

from solaris_ai_nn.homeostasis.needs import Need, NeedEstimator, NeedType
from solaris_ai_nn.homeostasis.variables import HomeostaticState


def _estimate(**variables):
    state = HomeostaticState()
    for name, value in variables.items():
        state.upsert(name, value)
    return NeedEstimator().estimate(state)


def test_energy_deficit_creates_restore_energy_need():
    need_state = _estimate(body_energy=0.15)
    need = need_state.by_type(NeedType.RESTORE_ENERGY)
    assert need is not None
    assert need.intensity > 0.4
    assert "body_energy" in need.source_variables
    assert "rest" in need.possible_desires
    # A full battery raises no energy need.
    assert _estimate(body_energy=0.9).by_type(
        NeedType.RESTORE_ENERGY) is None


def test_high_mysterium_creates_reduce_uncertainty_need():
    need_state = _estimate(unknown_pressure=0.8,
                           prediction_miss_pressure=0.7)
    need = need_state.by_type(NeedType.REDUCE_UNCERTAINTY)
    assert need is not None
    assert set(need.source_variables) == {"unknown_pressure",
                                          "prediction_miss_pressure"}
    assert need.confidence > 0.5
    assert "run_replay" in need.possible_desires


def test_policy_incident_creates_respect_boundary_need():
    need_state = _estimate(policy_violation_pressure=0.6,
                           blocked_action_pressure=0.5)
    need = need_state.by_type(NeedType.RESPECT_BOUNDARY)
    assert need is not None
    assert "remain_observe_only" in need.possible_desires


def test_danger_and_reward_needs():
    need_state = _estimate(danger_proximity=0.9, reward_proximity=0.8)
    assert need_state.by_type(NeedType.AVOID_DANGER) is not None
    assert need_state.by_type(NeedType.APPROACH_REWARD) is not None
    # Exhaustion marks the reward need inhibited (recorded, not dropped).
    inhibited = _estimate(reward_proximity=0.8, exhaustion_pressure=0.9,
                          body_energy=0.1)
    reward = inhibited.by_type(NeedType.APPROACH_REWARD)
    assert "exhaustion" in reward.inhibited_by


def test_dominant_need_and_evidence():
    need_state = _estimate(danger_proximity=0.95, low_stimulus_pressure=0.6)
    dominant = need_state.dominant()
    assert dominant.type == NeedType.AVOID_DANGER
    assert dominant.supporting_evidence[0]["variable"] == "danger_proximity"
    data = need_state.to_dict()
    assert data["note"].startswith("needs are internal pressure estimates")


def test_sidecar_context_creates_observe_only_need():
    state = HomeostaticState()
    need_state = NeedEstimator().estimate(state,
                                          {"sidecar_attached": True})
    assert need_state.by_type(NeedType.REMAIN_OBSERVE_ONLY) is not None


def test_unknown_need_type_rejected():
    with pytest.raises(ValueError):
        Need(type="conquer_world")
