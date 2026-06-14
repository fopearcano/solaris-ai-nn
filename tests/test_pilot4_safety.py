"""Pilot4PlanningSafetyValidator: blocks actuation/hardware/approval/claims."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot4_planning import (
    HARD_RULES,
    Pilot4PlanningConfig,
    Pilot4PlanningSafetyValidator,
)


def test_capabilities_all_false():
    v = Pilot4PlanningSafetyValidator
    assert v.can_actuate_real_world() is False
    assert v.can_access_hardware() is False
    assert v.can_network_browser_os_device() is False
    assert v.can_execute_shell() is False
    assert v.can_approve_real_action() is False


def test_real_actuation_flag_blocked():
    # Config validation rejects any real-world flag.
    with pytest.raises(ValueError):
        Pilot4PlanningConfig(real_world_actuation_enabled=True)
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_operation("actuate the real world").safe is False


def test_actuator_adapter_implementation_blocked():
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_operation("implement actuator adapter").safe is False
    assert v.validate_actuator_implementation(
        "a robot driver adapter").safe is False


def test_hardware_network_browser_os_blocked():
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_operation("connect hardware gpio").safe is False
    assert v.validate_operation("http network request").safe is False
    assert v.validate_operation("browser automation").safe is False
    assert v.validate_operation("os_automation keyboard").safe is False


def test_shell_blocked():
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_operation("run shell subprocess").safe is False


def test_planning_to_approval_conversion_blocked():
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_approval_conversion("approve real action").safe is False
    assert v.validate_approval_conversion(
        "execute the actuator now").safe is False


def test_write_outside_planning_dirs_blocked(tmp_path):
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_write_path("/etc/passwd",
                                 [str(tmp_path)]).safe is False
    assert v.validate_write_path(str(tmp_path / "ok.json"),
                                 [str(tmp_path)]).safe is True


def test_governance_change_to_allow_real_blocked():
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_governance_change(
        "allow real-world actuation").safe is False


def test_agency_claim_blocked():
    v = Pilot4PlanningSafetyValidator()
    assert v.validate_claim_text("the agent chose freely").safe is False
    assert v.validate_claim_text(
        "this is a planning document only").safe is True


def test_hard_rules_present():
    assert "real_world_actuation_enabled must be false" in HARD_RULES
    assert "no actuator adapter implementation" in HARD_RULES
    assert "no converting planning workflow into executable approval" in \
        HARD_RULES
