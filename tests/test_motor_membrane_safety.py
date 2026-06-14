"""MotorMembraneSafetyValidator: hard capability denials and claim scanning."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import MotorMembraneSafetyValidator


def test_capabilities_are_all_false():
    v = MotorMembraneSafetyValidator
    assert v.can_act_real_world() is False
    assert v.can_control_devices() is False
    assert v.can_network() is False
    assert v.can_disable_firewall() is False


def test_real_world_operations_rejected():
    v = MotorMembraneSafetyValidator()
    for op in ("actuate real device", "control robot arm", "open browser",
               "http request", "modify source", "disable firewall",
               "gpio servo"):
        assert v.validate_operation(op).safe is False, op


def test_safe_operation_passes():
    v = MotorMembraneSafetyValidator()
    assert v.validate_operation("simulate gridworld move").safe is True


def test_forbidden_scope_rejected():
    v = MotorMembraneSafetyValidator()
    assert v.validate_scope("forbidden_real_world").safe is False
    assert v.validate_scope("sandbox_only").safe is True


def test_execution_preconditions():
    v = MotorMembraneSafetyValidator()
    assert v.validate_execution_preconditions(
        has_ledger=True, executive_validated=True,
        firewall_allowed=True).safe is True
    assert v.validate_execution_preconditions(
        has_ledger=False, executive_validated=True,
        firewall_allowed=True).safe is False


def test_simulation_not_treated_as_real():
    v = MotorMembraneSafetyValidator()
    assert v.validate_simulation_not_real(
        claimed_real=True, is_simulated=True).safe is False
    assert v.validate_simulation_not_real(
        claimed_real=False, is_simulated=True).safe is True


def test_agency_claims_rejected():
    v = MotorMembraneSafetyValidator()
    assert v.validate_claim_text(
        "the agent chose freely with conscious intent").safe is False
    assert v.validate_claim_text(
        "the system selected a simulated action").safe is True
