"""Packaging detects fixture/live/console/feedback commands via the registry."""

from __future__ import annotations

from solaris_ai_nn.tester_packaging import CommandRegistryCheck


def _registered():
    return {c.name for c in CommandRegistryCheck().check().commands
            if c.registered}


def test_fixture_commands_detected():
    reg = _registered()
    for cmd in ("tester-demo", "tester-golden", "tester-bundle", "tester-repro",
                "tester-regression", "tester-fixtures"):
        assert cmd in reg, cmd


def test_live_tester_commands_detected():
    reg = _registered()
    for cmd in ("tester-live-init", "tester-live-doctor", "tester-live-samples",
                "tester-live-run", "tester-live-bundle"):
        assert cmd in reg, cmd


def test_console_command_detected():
    assert "tester-console" in _registered()
    assert "tester-console-status" in _registered()


def test_feedback_commands_detected():
    reg = _registered()
    for cmd in ("tester-feedback-init", "tester-feedback-report",
                "tester-feedback-ledger", "tester-feedback-bundle"):
        assert cmd in reg, cmd
