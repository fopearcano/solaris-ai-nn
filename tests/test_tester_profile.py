"""Tester profile: default loads, fixture-only, no live governance, bounded, membrane."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import (
    available_profiles,
    default_tester_profile,
    get_tester_profile,
)


def test_default_profile_loads():
    p = default_tester_profile()
    assert p.profile_id == "fixture_tester_v0"
    assert "fixture_tester_v0" in available_profiles()


def test_fixture_only_default():
    p = default_tester_profile()
    d = p.to_dict()
    assert d["fixture_only"] is True
    assert d["requires_live_data"] is False


def test_no_live_governance_required():
    p = default_tester_profile()
    assert p.governance_required is False
    assert p.feeders_required is False


def test_bounded_runtime_required():
    p = default_tester_profile()
    assert p.max_runtime_s > 0


def test_membrane_required_by_default():
    p = default_tester_profile()
    assert p.require_membrane is True
    assert p.require_impressions is True


def test_membrane_only_mode_disables_learning():
    p = get_tester_profile("fixture_membrane_only_v0")
    assert p.run_ontogenesis is False
    assert p.run_semiogenesis is False
    assert p.run_cognition is False


def test_unknown_profile_falls_back():
    p = get_tester_profile("nope")
    assert p.profile_id == "fixture_tester_v0"
    assert any("unknown" in l for l in p.limitations)
