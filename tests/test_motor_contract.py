"""MotorContractValidator: enforces the hard motor contract."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    MotorAction,
    MotorActionResult,
    MotorActionScope,
    MotorActionStatus,
    MotorActionType,
    MotorContractValidator,
)


def test_real_world_authority_rejected():
    v = MotorContractValidator()
    a = MotorAction(MotorActionType.MOVE_EAST)
    object.__setattr__(a, "real_world_authority", True)  # force the bad state
    assert v.validate_action(a)


def test_forbidden_scope_rejected():
    v = MotorContractValidator()
    a = MotorAction(MotorActionType.MOVE_EAST,
                    scope=MotorActionScope.FORBIDDEN_REAL_WORLD)
    assert v.validate_action(a)


def test_missing_executive_rejected():
    v = MotorContractValidator()
    a = MotorAction(MotorActionType.MOVE_EAST)
    assert v.validate_action(a, {"executive_validated": False})


def test_source_modification_rejected():
    v = MotorContractValidator()
    a = MotorAction(MotorActionType.MARK_SIMULATED_LOCATION)
    assert v.validate_action(a, {"modifies_source": True})


def test_safe_action_passes():
    v = MotorContractValidator()
    a = MotorAction(MotorActionType.LOOK, scope=MotorActionScope.SANDBOX_ONLY)
    assert v.validate_action(a) == []


def test_real_world_targets_rejected():
    v = MotorContractValidator()
    for target in ("/dev/ttyUSB0", "http://example.com", "robot_arm",
                   "sensory_source_1"):
        assert v.validate_target(target), target


def test_absolute_target_outside_roots_rejected(tmp_path):
    v = MotorContractValidator(sandbox_roots=[str(tmp_path)])
    assert v.validate_target("/somewhere/else/file")
    assert v.validate_target(str(tmp_path / "ok.json")) == []


def test_non_simulated_result_rejected():
    v = MotorContractValidator()
    r = MotorActionResult(action_id="x", action_type=MotorActionType.REST,
                          status=MotorActionStatus.EXECUTED_IN_SIMULATION)
    object.__setattr__(r, "simulated", False)
    assert v.validate_result(r)
