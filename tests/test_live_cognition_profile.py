"""Live cognition profile: default loads, no action, bounded, signs required."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import (
    available_profiles,
    default_cognition_profile,
    get_cognition_profile,
)


def test_default_profile_loads():
    p = default_cognition_profile()
    assert p.profile_id == "live_cognition_trace_v0"
    assert "live_cognition_trace_v0" in available_profiles()


def test_no_action_by_default():
    p = default_cognition_profile()
    assert p.action_enabled is False
    assert p.action_reaction_enabled is False
    assert p.developmental_autonomy_enabled is False
    assert p.self_boundary_enabled is False
    assert p.trace_only is True


def test_bounded_runtime_and_signs_required():
    p = default_cognition_profile()
    assert p.max_runtime_s > 0
    assert p.governance_required is True
    assert p.birth_certificate_required is True
    assert p.observation_stability_required is True
    assert p.concept_memory_required is True
    assert p.sign_memory_required is True


def test_anticipation_mode_allows_anticipation():
    p = get_cognition_profile("live_cognition_anticipation_limited_v0")
    assert p.allow_anticipation is True
    assert p.trace_only is False


def test_simulation_mode_allows_simulation():
    p = get_cognition_profile("live_cognition_internal_simulation_limited_v0")
    assert p.allow_internal_simulation is True
    assert p.allow_anticipation is True


def test_unknown_profile_falls_back():
    p = get_cognition_profile("nope")
    assert p.profile_id == "live_cognition_trace_v0"
    assert any("unknown" in l for l in p.limitations)
