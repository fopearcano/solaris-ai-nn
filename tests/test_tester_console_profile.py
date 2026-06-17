"""Tester console profile: default loads, static local default, no server, bounded."""

from __future__ import annotations

from solaris_ai_nn.tester_console import (
    available_profiles,
    default_console_profile,
    get_console_profile,
)


def test_default_profile_loads():
    p = default_console_profile()
    assert p.profile_id == "tester_console_static_v0"
    assert "tester_console_static_v0" in available_profiles()


def test_static_local_default():
    p = default_console_profile()
    d = p.to_dict()
    assert d["read_only"] is True
    assert d["runs_server"] is False
    assert d["opens_browser"] is False


def test_no_private_payloads_by_default():
    p = default_console_profile()
    assert p.include_private_payloads is False


def test_bounded_runtime_required():
    assert default_console_profile().max_runtime_s > 0


def test_markdown_only_mode_disables_html():
    p = get_console_profile("tester_console_markdown_only_v0")
    assert p.emit_html is False
    assert p.emit_markdown is True


def test_unknown_profile_falls_back():
    p = get_console_profile("nope")
    assert p.profile_id == "tester_console_static_v0"
    assert any("unknown" in l for l in p.limitations)
