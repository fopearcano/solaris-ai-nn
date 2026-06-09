"""Tests for the RollbackManager."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.plasticity.mutation import (
    PlasticityChange,
    PlasticityStep,
    PlasticityTarget,
    TargetRegistry,
)
from solaris_ai_nn.plasticity.rollback import RollbackManager


def _registry():
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=1)
    return bridge, TargetRegistry(bridge)


def _applied_step(registry, component, parameter, new):
    old = registry.get(PlasticityTarget(component, parameter))
    step = PlasticityStep(
        target=PlasticityTarget(component, parameter),
        change=PlasticityChange(old_value=old, new_value=new),
    )
    registry.set(step.target, new)  # actually apply
    return step


def test_rollback_restores_previous_value():
    bridge, reg = _registry()
    step = _applied_step(reg, "readout", "learning_rate", 0.9)
    assert bridge.learner.lr == 0.9

    mgr = RollbackManager()
    mgr.register(step)
    result = mgr.rollback(step.step_id, reg)
    assert result.applied is True
    assert result.status == "rolled_back"
    assert bridge.learner.lr == step.change.old_value


def test_rollback_logs_and_marks_record():
    _, reg = _registry()
    step = _applied_step(reg, "bridge", "exploration_tendency", 0.4)
    mgr = RollbackManager()
    mgr.register(step)
    mgr.rollback(step.step_id, reg)
    assert mgr.records[step.step_id].rolled_back is True
    # Second rollback fails gracefully (already rolled back).
    second = mgr.rollback(step.step_id, reg)
    assert second.applied is False


def test_rollback_unknown_step_fails_gracefully():
    _, reg = _registry()
    mgr = RollbackManager()
    result = mgr.rollback("does-not-exist", reg)
    assert result.applied is False
    assert result.status == "rollback_failed"
    assert "unknown" in result.message.lower()


def test_last_applied_and_to_dict():
    _, reg = _registry()
    s1 = _applied_step(reg, "readout", "learning_rate", 0.5)
    s2 = _applied_step(reg, "bridge", "exploration_tendency", 0.3)
    mgr = RollbackManager()
    mgr.register(s1)
    mgr.register(s2)
    assert mgr.last_applied().step_id == s2.step_id
    d = mgr.to_dict()
    assert d["count"] == 2
    assert len(d["steps"]) == 2
