"""Operator <-> Governance: scopes exist; console cannot change hard rules."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy


def test_governance_scopes_exist():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_OPERATOR_CONSOLE)
    assert ps.allows(PermissionScope.ENABLE_OPERATOR_PROFILE_PLANNING)
    assert ps.allows(PermissionScope.ENABLE_OPERATOR_BOUNDED_RUN_LAUNCH)
    assert ps.allows(PermissionScope.ENABLE_OPERATOR_EVIDENCE_NAVIGATION)
    assert ps.allows(PermissionScope.ENABLE_OPERATOR_EXPORT_BUNDLE)
    assert ps.allows(PermissionScope.ENABLE_OPERATOR_APPROVAL_LEDGER)


def test_default_operator_console_allowed():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"operator_console": True}})
    assert decision.allowed


def test_bounded_run_launch_requires_confirmation():
    pol = GovernancePolicy()
    without = pol.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"operator_console": True}},
        {"bounded_run_launch": True})
    assert not without.allowed
    with_confirm = pol.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"operator_console": True}},
        {"bounded_run_launch": True, "operator_confirmed": True})
    assert with_confirm.allowed


def test_console_cannot_change_hard_rules():
    pol = GovernancePolicy()
    for ctx in ({"shell_execution": True}, {"network_access": True},
                {"real_world_actuation": True},
                {"approve_forbidden_actuation": True},
                {"disable_safety": True}, {"delete_evidence": True},
                {"launch_prohibited_profile": True},
                {"unbounded_long_run": True}):
        decision = pol.evaluate_manifest(
            {"mode": "bounded", "enabled_features": {"operator_console": True}},
            ctx)
        assert not decision.allowed, ctx


def test_approval_ledger_cannot_approve_forbidden(tmp_path):
    from solaris_ai_nn.operator_console import ApprovalLedger, ApprovalScope

    record = ApprovalLedger(state_dir=str(tmp_path / "op")).record(
        ApprovalScope.FORBIDDEN_REAL_WORLD_ACTUATION, "no")
    assert record.recorded is False
