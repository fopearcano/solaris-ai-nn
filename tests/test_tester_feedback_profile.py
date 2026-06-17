"""Tester feedback profile: default loads, local-only, no training, bounded."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import (
    available_profiles,
    default_feedback_profile,
    get_feedback_profile,
)


def test_default_profile_loads():
    p = default_feedback_profile()
    assert p.profile_id == "tester_feedback_v0"
    assert "tester_feedback_v0" in available_profiles()


def test_local_only_default():
    d = default_feedback_profile().to_dict()
    assert d["local_only"] is True
    assert d["trains_on_feedback"] is False


def test_no_training_default():
    p = default_feedback_profile()
    assert "no_training" in p.constraints
    assert "no_rlhf" in p.constraints


def test_bounded_runtime_required():
    assert default_feedback_profile().max_runtime_s > 0


def test_forms_only_mode_disables_ingest():
    p = get_feedback_profile("tester_feedback_forms_only_v0")
    assert p.ingest_enabled is False


def test_unknown_profile_falls_back():
    p = get_feedback_profile("nope")
    assert p.profile_id == "tester_feedback_v0"
    assert any("unknown" in l for l in p.limitations)
