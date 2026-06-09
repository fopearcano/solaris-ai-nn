"""Tests for the PlasticityEngine."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.plasticity.mutation import (
    PlasticityChange,
    PlasticityStep,
    PlasticityTarget,
)
from solaris_ai_nn.plasticity.plasticity_engine import PlasticityEngine
from solaris_ai_nn.plasticity.synthesis_pruning import SynthesisPruner


def _engine(tmp_path, dry_run=False):
    bridge = SolarisNeuralBridge(action_labels=["a", "b", "c"], seed=1)
    return PlasticityEngine(
        bridge=bridge, synthesis=SynthesisPruner(), state_dir=str(tmp_path),
        run_id="r", session_id="s", dry_run=dry_run,
    )


def _step(component, parameter, new, old=0.0):
    return PlasticityStep(
        target=PlasticityTarget(component, parameter),
        change=PlasticityChange(old_value=old, new_value=new),
        run_id="r", session_id="s",
    )


def test_applies_safe_step(tmp_path):
    eng = _engine(tmp_path)
    step = _step("readout", "learning_rate", 0.5, old=eng.bridge.learner.lr)
    result = eng.apply(step)
    assert result.applied is True
    assert eng.bridge.learner.lr == 0.5
    assert eng.applied_count == 1
    assert eng.last_applied is step


def test_rejects_unsafe_step(tmp_path):
    eng = _engine(tmp_path)
    result = eng.apply(_step("readout", "source_code", "x.py"))
    assert result.applied is False
    assert result.status == "rejected"
    assert eng.rejected_count == 1


def test_dry_run_does_not_apply(tmp_path):
    eng = _engine(tmp_path, dry_run=True)
    before = eng.bridge.learner.lr
    result = eng.apply(_step("readout", "learning_rate", 0.9, old=before))
    assert result.applied is False
    assert eng.bridge.learner.lr == before
    assert eng.applied_count == 0


def test_logs_applied_and_rejected(tmp_path):
    eng = _engine(tmp_path)
    eng.apply(_step("readout", "learning_rate", 0.5, old=eng.bridge.learner.lr))
    eng.apply(_step("readout", "source_code", "x.py"))
    rows = eng.audit.read_all()
    types = [r["event_type"] for r in rows]
    assert "applied" in types
    assert "rejected" in types


def test_snapshot_fields(tmp_path):
    eng = _engine(tmp_path)
    eng.apply(_step("bridge", "exploration_tendency", 0.2, old=eng.bridge.exploration))
    snap = eng.snapshot()
    for key in ("applied_count", "rejected_count", "rollback_count",
                "current_parameters", "safety_status", "audit_path", "dry_run"):
        assert key in snap
    assert snap["applied_count"] == 1
    assert "bridge.exploration_tendency" in snap["current_parameters"]


def test_propose_uses_policy(tmp_path):
    eng = _engine(tmp_path)
    # Force a high-error streak so the policy proposes a learning-rate increase.
    eng._error_high_streak = 5
    ctx = eng.build_context()
    ctx["error_high_streak"] = 5
    steps = eng.propose(ctx)
    assert any(s.target.parameter == "learning_rate" for s in steps)
