"""EmbodimentSandboxRuntime: the one gated, simulation-only motor pipeline."""

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


def test_simulated_action_executes_in_sandbox(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.SANDBOX_ONLY))
    assert out["executed"] is True
    assert out["status"] == MotorActionStatus.EXECUTED_IN_SIMULATION
    assert rt.simulated_action_count == 1


def test_real_world_action_is_blocked(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    assert out["executed"] is False
    assert out["status"] in MotorActionStatus.BLOCKED
    assert rt.firewall.blocked_real_world_count == 1


def test_source_modification_is_blocked(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.MARK_SIMULATED_LOCATION),
                    {"modifies_source": True})
    assert out["executed"] is False


def test_dry_run_records_without_executing(tmp_path):
    rt = _runtime(tmp_path, dry_run=True)
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.SANDBOX_ONLY))
    assert out["executed"] is False
    assert out["status"] == MotorActionStatus.DRY_RUN_RECORDED
    assert rt.simulated_action_count == 0
    assert rt.dry_run_action_count == 1


def test_emergency_mode_blocks_movement(tmp_path):
    rt = _runtime(tmp_path)
    rt.request_emergency_stop()
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.SANDBOX_ONLY))
    assert out["executed"] is False


def test_proposal_logged_before_gates(tmp_path):
    rt = _runtime(tmp_path)
    rt.submit(MotorAction(MotorActionType.FORBIDDEN_REAL_WORLD
                          if False else MotorActionType.MOVE_EAST,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    # Even a blocked action is recorded in the ledger first.
    assert rt.ledger.proposed_count == 1


def test_summary_invariants(tmp_path):
    rt = _runtime(tmp_path)
    s = rt.summary()
    assert s["enabled"] is True
    assert s["real_world_authority"] is False
    assert s["firewall_enabled"] is True
    assert s["firewall_can_be_disabled"] is False
    assert s["sandbox_health"] == "ok"


def test_step_respects_max_actions_per_step(tmp_path):
    rt = _runtime(tmp_path, max_actions_per_step=1)
    out = rt.step([MotorAction(MotorActionType.MOVE_EAST,
                               scope=MotorActionScope.SANDBOX_ONLY),
                   MotorAction(MotorActionType.MOVE_WEST,
                               scope=MotorActionScope.SANDBOX_ONLY)])
    assert len(out) == 1
    assert rt.step_count == 1
