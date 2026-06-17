"""Live ontogenesis profile: default loads, no semiogenesis, bounded, gated."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import (
    available_profiles,
    default_ontogenesis_profile,
    get_ontogenesis_profile,
)


def test_default_profile_loads():
    p = default_ontogenesis_profile()
    assert p.profile_id == "live_ontogenesis_candidate_v0"
    assert "live_ontogenesis_candidate_v0" in available_profiles()


def test_no_semiogenesis_by_default():
    p = default_ontogenesis_profile()
    assert p.semiogenesis_enabled is False
    assert p.action_reaction_enabled is False
    assert p.developmental_autonomy_enabled is False
    assert p.candidate_only is True


def test_bounded_runtime_and_gates_required():
    p = default_ontogenesis_profile()
    assert p.max_runtime_s > 0
    assert p.governance_required is True
    assert p.birth_certificate_required is True
    assert p.observation_stability_required is True


def test_birth_limited_profile_allows_birth():
    p = get_ontogenesis_profile("live_ontogenesis_birth_limited_v0")
    assert p.allow_limited_birth is True
    assert p.candidate_only is False


def test_unknown_profile_falls_back():
    p = get_ontogenesis_profile("nope")
    assert p.profile_id == "live_ontogenesis_candidate_v0"
    assert any("unknown" in l for l in p.limitations)
