"""RC profile: default loads, local-only, no publish/upload, bounded required."""

from __future__ import annotations

from solaris_ai_nn.tester_release_candidate import (
    DEFAULT_PROFILE_ID,
    TesterRCConstraint,
    TesterRCMode,
    available_profiles,
    default_rc_profile,
    get_rc_profile,
)


def test_default_profile_loads():
    p = default_rc_profile()
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert p.mode == TesterRCMode.TESTER_RC_FULL
    d = p.to_dict()
    assert d["local_only"] is True
    assert d["assembly_only"] is True


def test_local_only_no_publish():
    d = default_rc_profile().to_dict()
    assert d["publishes"] is False
    c = default_rc_profile().constraints
    assert TesterRCConstraint.LOCAL_ONLY in c
    assert TesterRCConstraint.NO_PUBLIC_RELEASE in c
    assert TesterRCConstraint.NO_PACKAGE_UPLOAD in c
    assert TesterRCConstraint.NO_GIT_RELEASE_AUTOMATION in c


def test_bounded_runtime_required():
    p = default_rc_profile()
    assert p.max_runtime_s > 0
    assert TesterRCConstraint.BOUNDED_RUNTIME in p.constraints


def test_named_profiles_and_modes():
    profiles = available_profiles()
    assert DEFAULT_PROFILE_ID in profiles
    manifest = get_rc_profile("tester_rc_manifest_only_v0")
    assert manifest.build_manifest is True
    assert manifest.build_bundle is False
    docs = get_rc_profile("tester_rc_docs_only_v0")
    assert docs.build_docs is True


def test_unknown_profile_falls_back():
    p = get_rc_profile("does_not_exist")
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert any("unknown" in lim for lim in p.limitations)
