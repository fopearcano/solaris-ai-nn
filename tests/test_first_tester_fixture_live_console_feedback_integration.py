"""First tester integration: fixture-first, live optional, console, feedback."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import FirstTesterSessionScript


def test_fixture_first_requirement_present():
    text = FirstTesterSessionScript().build_text().lower()
    assert text.index("fixture demo") < text.index("live-read-only")


def test_live_optional_commands_present():
    text = FirstTesterSessionScript().build_text()
    assert "tester-live-init" in text
    assert "tester-live-doctor" in text
    assert "tester-live-samples" in text
    assert "tester-live-run" in text


def test_console_inspection_present():
    text = FirstTesterSessionScript().build_text()
    assert "tester-console" in text
    assert "INDEX.md" in text


def test_feedback_bundle_present():
    text = FirstTesterSessionScript().build_text()
    assert "tester-feedback-init" in text
    assert "tester-feedback-bundle" in text
