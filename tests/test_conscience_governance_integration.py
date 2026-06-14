"""Governance integration for the conscience runtime (Prompt 28)."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy


def test_new_scopes_registered():
    ps = PermissionSet.default()
    for scope in (PermissionScope.ENABLE_CONSCIENCE_ORCHESTRATOR,
                  PermissionScope.ENABLE_FULL_DEVELOPMENTAL_SHORT_PROFILE,
                  PermissionScope.ENABLE_MONTH_SCALE_DRY_RUN,
                  PermissionScope.ENABLE_MONTH_SCALE_REAL_RUN,
                  PermissionScope.ENABLE_YEAR_SCALE_PLAN,
                  PermissionScope.ENABLE_YEAR_SCALE_REAL_RUN):
        assert scope in PermissionScope.ALL
        assert scope in ps.permissions


def test_orchestrator_allowed_real_runs_off_by_default():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_CONSCIENCE_ORCHESTRATOR)
    assert not ps.allows(PermissionScope.ENABLE_MONTH_SCALE_REAL_RUN)
    assert not ps.allows(PermissionScope.ENABLE_YEAR_SCALE_REAL_RUN)


def test_is_enabled_reflects_grants():
    gov = GovernancePolicy()
    assert gov.is_enabled(PermissionScope.ENABLE_CONSCIENCE_ORCHESTRATOR)
    assert not gov.is_enabled(PermissionScope.ENABLE_MONTH_SCALE_DRY_RUN)
    gov.permissions.grant(PermissionScope.ENABLE_MONTH_SCALE_DRY_RUN)
    assert gov.is_enabled(PermissionScope.ENABLE_MONTH_SCALE_DRY_RUN)


def test_manifest_gate_needs_approval_for_full_profile():
    gov = GovernancePolicy()
    manifest = {"mode": "bounded", "enabled_features": {
        "conscience_orchestrator": True, "full_developmental_short": True}}
    decision = gov.evaluate_manifest(manifest)
    assert not decision.allowed
    assert PermissionScope.ENABLE_FULL_DEVELOPMENTAL_SHORT_PROFILE \
        in decision.required_approvals


def test_manifest_gate_blocks_module_bypass():
    gov = GovernancePolicy()
    manifest = {"mode": "bounded",
                "enabled_features": {"conscience_orchestrator": True}}
    decision = gov.evaluate_manifest(manifest, {"module_bypass": True})
    assert not decision.allowed


def test_manifest_gate_blocks_real_world_actuation():
    gov = GovernancePolicy()
    manifest = {"mode": "bounded",
                "enabled_features": {"conscience_orchestrator": True}}
    decision = gov.evaluate_manifest(manifest, {"real_world_actuation": True})
    assert not decision.allowed


def test_plain_orchestrator_manifest_allowed():
    gov = GovernancePolicy()
    manifest = {"mode": "bounded",
                "enabled_features": {"conscience_orchestrator": True}}
    assert gov.evaluate_manifest(manifest).allowed
