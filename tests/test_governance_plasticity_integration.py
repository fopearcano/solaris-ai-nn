"""Tests for governance wired into the PlasticityEngine."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.governance import (
    ApprovalRegistry,
    GovernancePolicy,
    PermissionScope,
)
from solaris_ai_nn.plasticity.mutation import (
    PlasticityChange,
    PlasticityStep,
    PlasticityTarget,
)
from solaris_ai_nn.plasticity.plasticity_engine import PlasticityEngine


def _step():
    return PlasticityStep(
        target=PlasticityTarget("readout", "learning_rate"),
        change=PlasticityChange(old_value=None, new_value=0.05,
                                expected_effect="faster adaptation"),
        reason="test", trigger_source="experimental")


def _engine(tmp_path, governance, dry_run=False):
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=1)
    return PlasticityEngine(
        bridge=bridge, governance=governance, dry_run=dry_run,
        audit_path=str(tmp_path / "audit.jsonl"))


def test_active_plasticity_blocked_without_approval(tmp_path):
    engine = _engine(tmp_path, GovernancePolicy())
    result = engine.apply(_step())
    assert not result.applied
    assert result.status == "rejected"
    assert "governance" in result.message
    assert engine.governance_rejected_count == 1


def test_dry_run_plasticity_allowed(tmp_path):
    engine = _engine(tmp_path, GovernancePolicy(), dry_run=True)
    result = engine.apply(_step())
    # Dry-run scope is granted by default: validated, not applied.
    assert not result.applied
    assert result.status == "proposed"
    assert engine.governance_rejected_count == 0


def test_approved_plasticity_proceeds(tmp_path):
    approvals = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = approvals.request_approval(
        PermissionScope.ENABLE_PLASTICITY_APPLY, reason="test")
    approvals.approve(request.request_id, "tester")
    engine = _engine(tmp_path, GovernancePolicy(approvals=approvals))
    result = engine.apply(_step())
    assert result.applied
    assert result.status == "applied"
    assert engine.applied_count == 1


def test_source_rewriting_blocked_even_with_approval(tmp_path):
    approvals = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = approvals.request_approval(
        PermissionScope.ENABLE_PLASTICITY_APPLY, reason="test")
    approvals.approve(request.request_id, "tester")
    engine = _engine(tmp_path, GovernancePolicy(approvals=approvals))
    # The safety validator already forbids this; governance is a second wall.
    step = PlasticityStep(
        target=PlasticityTarget("readout", "source_file"),
        change=PlasticityChange(old_value=None, new_value="evil.py"),
        reason="attack", trigger_source="experimental")
    result = engine.apply(step)
    assert not result.applied


def test_no_governance_falls_back_to_safety(tmp_path):
    # Without a governance object, the engine behaves as before (Prompt 5).
    engine = _engine(tmp_path, None)
    result = engine.apply(_step())
    assert result.applied  # safety validator allows it; no governance gate
    assert engine.snapshot()["governance_enabled"] is False


def test_snapshot_reports_governance_decision(tmp_path):
    engine = _engine(tmp_path, GovernancePolicy())
    engine.apply(_step())
    snap = engine.snapshot()
    assert snap["governance_enabled"] is True
    assert snap["governance_rejected_count"] == 1
    assert snap["last_governance_decision"]["allowed"] is False
