"""Tester live profile: default loads, governance/feeder required, bounded, no control."""

from __future__ import annotations

from solaris_ai_nn.tester_live_readonly import (
    available_profiles,
    default_live_tester_profile,
    get_live_tester_profile,
)


def test_default_profile_loads():
    p = default_live_tester_profile()
    assert p.profile_id == "tester_live_readonly_v0"
    assert "tester_live_readonly_v0" in available_profiles()


def test_governance_required():
    assert default_live_tester_profile().governance_required is True


def test_feeder_registry_required():
    assert default_live_tester_profile().feeder_registry_required is True


def test_bounded_runtime_required():
    assert default_live_tester_profile().max_runtime_s > 0


def test_no_feeder_control():
    d = default_live_tester_profile().to_dict()
    assert d["solaris_starts_feeders"] is False
    assert d["external_feeders_only"] is True
    assert d["live_read_only"] is True


def test_membrane_required():
    assert default_live_tester_profile().require_membrane is True


def test_init_only_mode_disables_stages():
    p = get_live_tester_profile("tester_live_init_only_v0")
    assert p.run_birth is False
    assert p.run_membrane is False
    assert p.run_observation is False


def test_unknown_profile_falls_back():
    p = get_live_tester_profile("nope")
    assert p.profile_id == "tester_live_readonly_v0"
    assert any("unknown" in l for l in p.limitations)
