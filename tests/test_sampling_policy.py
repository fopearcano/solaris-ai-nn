"""Tests for the sampling policy."""

from __future__ import annotations

from solaris_ai_nn.active_perception.sampling_policy import (
    SamplingPolicy,
    SamplingPolicyMode,
)


def _ctx(**kw):
    ctx = {"step": 0, "mysterium_pressure": 0.6,
           "world_model": {"graph_node_count": 10, "unknown_node_count": 3,
                           "prediction_accuracy": 0.5},
           "health_level": "ok", "energy": 0.9}
    ctx.update(kw)
    return ctx


def test_balanced_selects_safe_action():
    policy = SamplingPolicy(mode=SamplingPolicyMode.BALANCED, seed=7)
    decision = policy.select_best_action(_ctx())
    assert decision.mode == SamplingPolicyMode.BALANCED
    assert decision.action.scope in ("simulation_only", "internal_only")


def test_emergency_selects_no_sampling():
    policy = SamplingPolicy(mode=SamplingPolicyMode.BALANCED, seed=7)
    decision = policy.select_best_action(_ctx(emergency=True))
    assert decision.mode == SamplingPolicyMode.EMERGENCY
    assert decision.action.action_type == "no_sampling_action"


def test_critical_health_forces_emergency():
    policy = SamplingPolicy(mode=SamplingPolicyMode.CURIOSITY_DRIVEN, seed=7)
    decision = policy.select_best_action(_ctx(health_level="critical"))
    assert decision.mode == SamplingPolicyMode.EMERGENCY


def test_conservative_avoids_unknown_region():
    policy = SamplingPolicy(mode=SamplingPolicyMode.CONSERVATIVE, seed=7)
    actions = policy.select_actions(_ctx(mysterium_pressure=0.9))
    types = {a.action_type for a in actions}
    assert "sample_unknown_region" not in types
    assert "seek_novelty" not in types


def test_passive_proposes_nothing_active():
    policy = SamplingPolicy(mode=SamplingPolicyMode.PASSIVE, seed=7)
    decision = policy.select_best_action(_ctx())
    assert decision.action.action_type == "no_sampling_action"


def test_deterministic_with_seed():
    a = SamplingPolicy(mode="balanced", seed=11).select_actions(_ctx())
    b = SamplingPolicy(mode="balanced", seed=11).select_actions(_ctx())
    assert [x.action_type for x in a] == [x.action_type for x in b]


def test_unknown_mode_rejected():
    import pytest

    with pytest.raises(ValueError):
        SamplingPolicy(mode="telepathy")
