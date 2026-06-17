"""First tester protocol profile: default, fixture-first, live optional, bounded."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import (
    DEFAULT_PROFILE_ID,
    FirstTesterProtocolConstraint,
    FirstTesterProtocolMode,
    available_profiles,
    default_protocol_profile,
    get_protocol_profile,
)


def test_default_profile_loads():
    p = default_protocol_profile()
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert p.mode == FirstTesterProtocolMode.FIRST_TESTER_PROTOCOL_FULL
    d = p.to_dict()
    assert d["local_only"] is True
    assert d["documentation_only"] is True
    assert d["runs_session"] is False


def test_fixture_first_default():
    p = default_protocol_profile()
    assert p.fixture_first is True
    assert FirstTesterProtocolConstraint.FIXTURE_FIRST_REQUIRED in p.constraints


def test_live_optional_default():
    p = default_protocol_profile()
    assert p.live_readonly_optional is True
    assert FirstTesterProtocolConstraint.LIVE_READONLY_OPTIONAL in p.constraints


def test_bounded_runtime_required():
    p = default_protocol_profile()
    assert p.max_runtime_s > 0
    assert FirstTesterProtocolConstraint.NO_PUBLIC_RELEASE in p.constraints


def test_named_profiles():
    profiles = available_profiles()
    assert DEFAULT_PROFILE_ID in profiles
    script = get_protocol_profile("first_tester_script_only_v0")
    assert script.generate_script is True
    assert script.generate_handoff is False


def test_unknown_profile_falls_back():
    p = get_protocol_profile("does_not_exist")
    assert p.profile_id == DEFAULT_PROFILE_ID
    assert any("unknown" in lim for lim in p.limitations)
