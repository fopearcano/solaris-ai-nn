"""Command registry check: required/optional checked, missing required blocks."""

from __future__ import annotations

from solaris_ai_nn.tester_packaging import CommandRegistryCheck
from solaris_ai_nn.tester_packaging.command_registry_check import (
    CommandCheckResult,
    RegisteredCommand,
)


def test_required_commands_checked():
    result = CommandRegistryCheck().check()
    names = {c.name for c in result.commands if c.required}
    assert "tester-demo" in names
    assert "membrane-run" in names
    assert "tester-feedback-init" in names


def test_optional_commands_checked():
    result = CommandRegistryCheck().check()
    names = {c.name for c in result.commands if not c.required}
    assert "live-birth" in names


def test_all_required_registered_in_repo():
    # In this repo all required tester commands are registered.
    result = CommandRegistryCheck().check()
    assert result.passed is True
    assert result.missing_required == []


def test_missing_required_command_blocks():
    r = CommandCheckResult()
    r.commands.append(RegisteredCommand("tester-demo", True, registered=False))
    assert r.passed is False
    assert "tester-demo" in r.missing_required


def test_missing_optional_command_warns():
    r = CommandCheckResult()
    r.commands.append(RegisteredCommand("alpha-demo", False, registered=False))
    assert r.passed is True
    assert "alpha-demo" in r.missing_optional


def test_runs_no_commands():
    assert CommandRegistryCheck().check().to_dict()["runs_commands"] is False
