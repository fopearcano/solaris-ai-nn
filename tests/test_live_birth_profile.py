"""Live birth profile: default loads, governance required, bounded, forbidden."""

from __future__ import annotations

from solaris_ai_nn.live_birth import (
    DEFAULT_PROFILE_ID,
    FORBIDDEN_FIRST_BIRTH_SOURCES,
    default_live_birth_profile,
    get_live_birth_profile,
)


def test_default_profile_loads():
    p = default_live_birth_profile()
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert get_live_birth_profile().profile_id == DEFAULT_PROFILE_ID
    assert get_live_birth_profile(None).profile_id == DEFAULT_PROFILE_ID


def test_governance_required():
    p = default_live_birth_profile()
    assert p.governance_required is True
    assert p.birth_certificate_required is True


def test_profile_bounded():
    p = default_live_birth_profile()
    assert p.max_runtime_s > 0
    assert p.max_events > 0
    assert p.max_files > 0


def test_forbidden_sources_blocked():
    p = default_live_birth_profile()
    for src in FORBIDDEN_FIRST_BIRTH_SOURCES:
        assert p.source_allowed(src) is False
    assert p.source_allowed("chronos_absence") is True


def test_live_readonly_default():
    p = default_live_birth_profile()
    assert p.live_readonly is True
    assert p.is_live is True


def test_unknown_profile_falls_back():
    p = get_live_birth_profile("does_not_exist")
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert any("unknown" in l for l in p.limitations)
