"""Packaging profile: default loads, local-only, no publish/upload, bounded."""

from __future__ import annotations

from solaris_ai_nn.tester_packaging import (
    available_profiles,
    default_packaging_profile,
    get_packaging_profile,
)


def test_default_profile_loads():
    p = default_packaging_profile()
    assert p.profile_id == "tester_packaging_v0"
    assert "tester_packaging_v0" in available_profiles()


def test_local_only_default():
    d = default_packaging_profile().to_dict()
    assert d["local_only"] is True
    assert d["installs_packages"] is False
    assert d["publishes"] is False


def test_no_publish_upload_constraints():
    p = default_packaging_profile()
    assert "no_upload" in p.constraints
    assert "no_publish" in p.constraints
    assert "no_global_install" in p.constraints


def test_bounded_runtime_required():
    assert default_packaging_profile().max_runtime_s > 0


def test_doctor_mode_skips_guides():
    p = get_packaging_profile("tester_packaging_doctor_v0")
    assert p.build_guides is False
    assert p.build_manifest is False


def test_unknown_profile_falls_back():
    p = get_packaging_profile("nope")
    assert p.profile_id == "tester_packaging_v0"
    assert any("unknown" in l for l in p.limitations)
