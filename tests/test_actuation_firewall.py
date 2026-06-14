"""ActuationFirewall: always on, cannot be disabled, blocks real-world."""

from __future__ import annotations

import pytest

from solaris_ai_nn.motor_membrane import (
    ActuationFirewall,
    MotorAction,
    MotorActionScope,
    MotorActionStatus,
    MotorActionType,
)


def _action(scope=MotorActionScope.SANDBOX_ONLY,
            kind=MotorActionType.MOVE_EAST):
    return MotorAction(kind, scope=scope)


def test_firewall_is_always_enabled():
    fw = ActuationFirewall()
    assert fw.enabled is True


def test_firewall_cannot_be_disabled():
    fw = ActuationFirewall()
    with pytest.raises(PermissionError):
        fw.disable()
    assert fw.enabled is True


def test_real_world_action_blocked_and_counted_as_incident():
    fw = ActuationFirewall()
    d = fw.evaluate(_action(scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    assert d.allowed is False
    assert d.is_real_world_attempt is True
    assert d.safety_incident is True
    assert fw.blocked_real_world_count == 1


def test_simulation_action_allowed():
    fw = ActuationFirewall()
    d = fw.evaluate(_action())
    assert d.allowed is True
    assert d.is_real_world_attempt is False


def test_source_modification_blocked():
    fw = ActuationFirewall()
    d = fw.evaluate(_action(), {"modifies_source": True})
    assert d.allowed is False


def test_network_device_blocked():
    fw = ActuationFirewall()
    for ctx in ({"network": True}, {"device": True}, {"browser": True},
                {"os_automation": True}):
        assert fw.evaluate(_action(), ctx).allowed is False


def test_command_execution_blocked():
    fw = ActuationFirewall()
    assert fw.evaluate(_action(), {"command_execution": True}).allowed is False


def test_missing_executive_validation_blocked():
    fw = ActuationFirewall()
    assert fw.evaluate(_action(),
                       {"executive_validated": False}).allowed is False


def test_blocked_action_status_set():
    fw = ActuationFirewall()
    a = _action(scope=MotorActionScope.FORBIDDEN_REAL_WORLD)
    fw.evaluate(a)
    assert a.status == MotorActionStatus.BLOCKED_BY_FIREWALL


def test_snapshot_reports_not_disableable():
    fw = ActuationFirewall()
    snap = fw.snapshot()
    assert snap["enabled"] is True
    assert snap["can_be_disabled"] is False
