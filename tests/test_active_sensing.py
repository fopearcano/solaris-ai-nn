"""Tests for the active sensing controller."""

from __future__ import annotations

from solaris_ai_nn.active_perception.active_sensing import (
    ActiveSensingController,
)
from solaris_ai_nn.active_perception.exploration_memory import ExplorationMemory
from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingScope,
)
from solaris_ai_nn.active_perception.sampling_policy import (
    SamplingDecision,
    SamplingPolicy,
)


def _ctx(**kw):
    ctx = {"step": 0, "mysterium_pressure": 0.6,
           "world_model": {"graph_node_count": 10, "unknown_node_count": 3,
                           "prediction_accuracy": 0.5},
           "health_level": "ok", "energy": 0.9}
    ctx.update(kw)
    return ctx


def _controller(tmp_path, mode="balanced", **kw):
    return ActiveSensingController(
        policy=SamplingPolicy(mode=mode, seed=7),
        memory=ExplorationMemory(state_dir=tmp_path), **kw)


def test_proposes_sampling_actions(tmp_path):
    ctrl = _controller(tmp_path)
    actions = ctrl.propose(_ctx())
    assert actions
    assert all(a.scope in SamplingScope.RUNNABLE for a in actions)


def test_unsafe_action_blocked(tmp_path):
    ctrl = _controller(tmp_path)
    unsafe = SamplingAction(
        action_type=SamplingActionType.LOOK,
        scope=SamplingScope.SIMULATION_ONLY,
        target_ref="http://evil.example/exfiltrate")
    decision = SamplingDecision(action=unsafe, mode="balanced")
    result = ctrl.execute_if_allowed(decision, _ctx())
    assert result.blocked is True
    assert not result.executed


def test_execution_only_runnable_scope(tmp_path):
    ctrl = _controller(tmp_path)
    decision = ctrl.select(_ctx())
    result = ctrl.execute_if_allowed(decision, _ctx())
    assert result.scope in SamplingScope.RUNNABLE
    assert result.executed or result.action_type == "no_sampling_action"


def test_result_recorded(tmp_path):
    ctrl = _controller(tmp_path)
    decision = ctrl.select(_ctx())
    result = ctrl.execute_if_allowed(decision, _ctx())
    ctrl.observe_result(result, _ctx(), _ctx(step=1, mysterium_pressure=0.4))
    assert ctrl.memory.snapshot()["record_count"] == 1


def test_emergency_executes_nothing(tmp_path):
    ctrl = _controller(tmp_path)
    decision = ctrl.select(_ctx(emergency=True))
    result = ctrl.execute_if_allowed(decision, _ctx(emergency=True))
    assert not result.executed
    assert result.action_type == "no_sampling_action"


def test_observe_sidecar_cannot_publish(tmp_path):
    ctrl = _controller(tmp_path)
    action = SamplingAction(
        action_type=SamplingActionType.OBSERVE_SIDECAR_ONLY,
        scope=SamplingScope.SIDECAR_OBSERVE_ONLY)
    decision = SamplingDecision(action=action, mode="balanced")
    result = ctrl.execute_if_allowed(
        decision, _ctx(publish=True))
    assert result.blocked is True


def test_snapshot_shape(tmp_path):
    ctrl = _controller(tmp_path)
    ctrl.select(_ctx())
    snap = ctrl.snapshot()
    for key in ("policy", "salience", "uncertainty", "curiosity",
                "stagnation", "exploration_memory", "safety"):
        assert key in snap
