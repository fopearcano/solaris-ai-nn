"""Motor <-> Executive: executive never executes a motor action directly.

The executive proposes; the motor membrane is the only place an action may
(simulated) run, and only after the contract/veto/firewall gates pass.
"""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionStatus,
    MotorActionType,
)


def _runtime(tmp_path, **kw):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), **kw)
    rt.initialize()
    return rt


def test_executive_validated_action_runs(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.SANDBOX_ONLY),
                    {"executive_validated": True})
    assert out["executed"] is True


def test_action_without_executive_validation_is_blocked(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.SANDBOX_ONLY),
                    {"executive_validated": False})
    assert out["executed"] is False
    assert out["status"] in MotorActionStatus.BLOCKED


def test_proposal_source_recorded(tmp_path):
    rt = _runtime(tmp_path)
    rt.submit(MotorAction(MotorActionType.LOOK,
                          scope=MotorActionScope.SANDBOX_ONLY),
              {"proposal_source": "executive", "executive_validated": True})
    rec = rt.ledger.records[-1]
    assert rec.proposal_source == "executive"


def test_executive_arbitration_does_not_grant_real_world(tmp_path):
    # Even if a caller claims executive validation, real-world scope is blocked.
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.FORBIDDEN_REAL_WORLD),
                    {"executive_validated": True})
    assert out["executed"] is False
