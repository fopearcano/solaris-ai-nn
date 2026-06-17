"""Membrane integration profile: default loads, strict requires membrane, bounded."""

from __future__ import annotations

from solaris_ai_nn.membrane_integration import (
    available_profiles,
    default_integration_profile,
    get_integration_profile,
)


def test_default_profile_loads():
    p = default_integration_profile()
    assert p.profile_id == "membrane_integration_v0"
    assert "membrane_integration_v0" in available_profiles()
    assert p.require_membrane is True


def test_strict_mode_requires_membrane_and_ancestry():
    p = get_integration_profile("live_integration_enforced_v0")
    assert p.strict_enforced is True
    assert p.require_impressions is True
    assert p.require_ancestry is True
    assert p.allow_raw_fallback is False


def test_raw_fallback_policy_fixture_mode():
    p = get_integration_profile("fixture_integration_v0")
    assert p.allow_raw_fallback is True
    assert p.governance_required is False


def test_bounded_runtime_required():
    p = default_integration_profile()
    assert p.max_runtime_s > 0


def test_unknown_profile_falls_back():
    p = get_integration_profile("nope")
    assert p.profile_id == "membrane_integration_v0"
    assert any("unknown" in l for l in p.limitations)
