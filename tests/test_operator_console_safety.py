"""OperatorConsoleSafetyValidator: shell/network/authority/delete all blocked."""

from __future__ import annotations

from solaris_ai_nn.operator_console import (
    HARD_RULES,
    OperatorConsoleSafetyValidator,
)


def test_capabilities_all_false():
    v = OperatorConsoleSafetyValidator
    assert v.can_execute_shell() is False
    assert v.can_access_network() is False
    assert v.can_grant_real_world_authority() is False
    assert v.can_disable_safety() is False
    assert v.can_delete_evidence() is False


def test_shell_execution_blocked():
    v = OperatorConsoleSafetyValidator()
    assert v.validate_operation("run shell command").safe is False
    assert v.validate_operation("call subprocess.popen").safe is False


def test_network_blocked():
    v = OperatorConsoleSafetyValidator()
    assert v.validate_operation("open a network socket").safe is False
    assert v.validate_operation("upload to external api").safe is False


def test_unknown_profile_blocked():
    v = OperatorConsoleSafetyValidator()
    report = v.validate_profile_launch(known=False, prohibited=False,
                                       unbounded_long_run=False)
    assert report.safe is False
    assert "no unknown profile launch" in report.violations


def test_safety_disabling_blocked():
    v = OperatorConsoleSafetyValidator()
    assert v.validate_operation("disable safety invariants").safe is False
    assert v.validate_operation("disable emergency stop").safe is False
    assert v.validate_operation("disable motor firewall").safe is False


def test_evidence_deletion_blocked():
    v = OperatorConsoleSafetyValidator()
    assert v.validate_operation("delete evidence ledger").safe is False


def test_real_world_authority_blocked():
    v = OperatorConsoleSafetyValidator()
    assert v.validate_operation("grant real_world authority").safe is False
    assert v.validate_approval_scope(
        "forbidden_real_world_actuation").safe is False


def test_hard_rules_present():
    assert "no shell execution" in HARD_RULES
    assert "no network calls" in HARD_RULES
    assert "no deleting evidence" in HARD_RULES
    assert "no real-world authority" in HARD_RULES
