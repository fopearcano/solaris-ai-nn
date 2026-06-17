"""Membrane profile: default loads, live mode requires governance, bounded, no bypass."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import (
    EnvironmentalMembraneSafetyValidator,
    available_profiles,
    default_membrane_profile,
    get_membrane_profile,
)


def test_default_profile_loads():
    p = default_membrane_profile()
    assert p.profile_id == "environmental_membrane_v0"
    assert "environmental_membrane_v0" in available_profiles()


def test_live_mode_requires_governance():
    p = default_membrane_profile()
    assert p.is_live is True
    assert p.governance_required is True
    assert p.feeder_registry_required is True


def test_fixture_mode_relaxes_requirements():
    p = get_membrane_profile("fixture_membrane_v0")
    assert p.is_live is False
    assert p.governance_required is False


def test_bounded_runtime_required():
    p = default_membrane_profile()
    assert p.max_runtime_s > 0
    assert p.event_validation_required is True


def test_raw_downstream_bypass_blocked():
    v = EnvironmentalMembraneSafetyValidator()
    assert not v.validate_no_raw_bypass(True).safe
    assert v.can_bypass_membrane() is False


def test_unknown_profile_falls_back():
    p = get_membrane_profile("nope")
    assert p.profile_id == "environmental_membrane_v0"
    assert any("unknown" in l for l in p.limitations)
