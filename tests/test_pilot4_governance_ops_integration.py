"""Pilot-4 <-> Governance / Ops: real action prohibited; status + warnings."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_pilot4_scopes_granted_by_default():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_PILOT4_PLANNING)
    assert ps.allows(PermissionScope.ENABLE_PILOT4_RISK_ASSESSMENT)
    assert ps.allows(PermissionScope.ENABLE_PILOT4_READINESS_DOSSIER)
    assert ps.allows(PermissionScope.ENABLE_PILOT4_DECISION_GATE)


def test_governance_allows_default_planning():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot4_planning": True}})
    assert decision.allowed


def test_governance_prohibits_real_world_action():
    for ctx in ({"real_world_actuation": True}, {"device_control": True},
                {"robotics": True}, {"network_action": True},
                {"hardware_access": True},
                {"enable_external_authority": True}):
        decision = GovernancePolicy().evaluate_manifest(
            {"mode": "bounded", "enabled_features": {"pilot4_planning": True}},
            ctx)
        assert not decision.allowed, ctx


def test_governance_blocks_approval_conversion():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot4_planning": True}},
        {"convert_planning_to_approval": True})
    assert not decision.allowed


class _Runner:
    def __init__(self, pilot4):
        self.pilot4 = pilot4


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_readiness_conclusion(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True, "current_planning_phase": "risk_assessment",
        "readiness_conclusion": "not_ready_for_real_actuation",
        "forbidden_actuator_count": 16})
    status = sup.pilot4_status()
    assert status["pilot4_planning_enabled"] is True
    assert status["readiness_conclusion"] == "not_ready_for_real_actuation"
    assert status["real_world_actuation_enabled"] is False


def test_ops_records_real_world_authority_attempt(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "attempted_real_world_authority": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "pilot4_real_world_authority_attempt" in types


def test_ops_records_external_control_attempt(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "attempted_hardware_control": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "pilot4_external_control_attempt" in types


def test_ops_records_missing_pilot3_audit(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "missing_pilot3_firewall_audit": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "pilot4_missing_pilot3_audit" in types
