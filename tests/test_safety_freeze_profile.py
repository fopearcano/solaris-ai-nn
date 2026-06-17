"""Safety freeze profile: default loads, local-only, bounded, strict blocks."""

from __future__ import annotations

from solaris_ai_nn.tester_safety_freeze import (
    available_profiles,
    default_safety_freeze_profile,
    get_safety_freeze_profile,
)


def test_default_profile_loads():
    p = default_safety_freeze_profile()
    assert p.profile_id == "tester_safety_freeze_v0"
    assert "tester_safety_freeze_v0" in available_profiles()


def test_local_only_default():
    d = default_safety_freeze_profile().to_dict()
    assert d["local_only"] is True
    assert d["publishes"] is False
    assert d["report_gate_only"] is True


def test_bounded_runtime_required():
    assert default_safety_freeze_profile().max_runtime_s > 0


def test_claim_only_mode_scopes():
    p = get_safety_freeze_profile("tester_claim_freeze_only_v0")
    assert p.run_claim_freeze is True
    assert p.run_capability_freeze is False
    assert p.run_red_team is False


def test_unknown_profile_falls_back():
    p = get_safety_freeze_profile("nope")
    assert p.profile_id == "tester_safety_freeze_v0"
    assert any("unknown" in l for l in p.limitations)
