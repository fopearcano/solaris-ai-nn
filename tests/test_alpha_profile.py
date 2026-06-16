"""Alpha profile: default loads, fixture default, live blocked, bounded."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import (
    DEFAULT_PROFILE_ID,
    default_alpha_profile,
    get_alpha_profile,
)


def test_default_profile_loads():
    p = default_alpha_profile()
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert get_alpha_profile().profile_id == DEFAULT_PROFILE_ID
    assert get_alpha_profile(None).profile_id == DEFAULT_PROFILE_ID


def test_fixture_mode_default():
    p = default_alpha_profile()
    assert p.fixture_mode_enabled is True
    assert p.live_read_only_allowed is False
    assert p.is_fixture_only is True


def test_live_mode_blocked_without_governance():
    p = default_alpha_profile()
    # Default profile does not allow live read-only at all.
    assert p.live_blocked(governance_present=True) is True
    assert p.live_blocked(governance_present=False) is True


def test_bounded_runtime_required():
    p = default_alpha_profile()
    assert p.max_runtime_s > 0
    assert p.max_ticks > 0


def test_unknown_profile_falls_back_to_default():
    p = get_alpha_profile("does_not_exist")
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert any("unknown" in l for l in p.limitations)
