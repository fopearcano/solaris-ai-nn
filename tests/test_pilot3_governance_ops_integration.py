"""Pilot-3 <-> Governance / Ops: real actuation prohibited; status + warnings."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_pilot3_scopes_granted_by_default():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_PILOT3_SOAK)
    assert ps.allows(PermissionScope.ENABLE_PILOT3_FIREWALL_PREFLIGHT)
    assert ps.allows(PermissionScope.ENABLE_PILOT3_POST_ANALYSIS)
    assert ps.requires_approval(
        PermissionScope.ENABLE_PILOT3_GRIDWORLD_SOAK_SIMULATED)


def test_governance_allows_default_soak():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot3_soak": True}})
    assert decision.allowed


def test_governance_prohibits_real_actuation():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot3_soak": True}},
        {"real_world_actuation": True})
    assert not decision.allowed


def test_governance_blocks_pilot4_real_actuation():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot3_soak": True}},
        {"pilot4_real_actuation": True})
    assert not decision.allowed


def test_gridworld_needs_firewall_preflight():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot3_soak": True},
         "pilot3_mode": "gridworld_short"},
        {"firewall_preflight_passed": False})
    assert not decision.allowed


class _Runner:
    def __init__(self, pilot3):
        self.pilot3 = pilot3


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_pilot3(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True, "pilot3_soak_phase": "gridworld_action_soak",
        "embodiment_condition": "gridworld_body", "action_count": 5,
        "veto_count": 1, "firewall_audit_status": "passed",
        "latest_action_grounding_quality": "moderate"})
    status = sup.pilot3_status()
    assert status["pilot3_soak_enabled"] is True
    assert status["pilot3_soak_phase"] == "gridworld_action_soak"
    assert status["real_world_authority"] is False


def test_ops_records_firewall_audit_critical(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "firewall_audit_critical_findings": 1})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "pilot3_firewall_audit_critical" in types


def test_ops_records_sandbox_overfit(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "sandbox_overfit_warning": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "pilot3_sandbox_overfit" in types


def test_ops_records_source_boundary_violation(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "source_boundary_violation": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "pilot3_source_boundary_violation" in types
