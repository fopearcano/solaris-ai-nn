"""Motor <-> Ego/Governance/Ops: attribution, gating, status, warnings."""

from __future__ import annotations

from solaris_ai_nn.ego.ownership import OwnershipAttributor
from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_motor_event_attributed_as_simulated_action():
    attr = OwnershipAttributor()
    result = attr.attribute_event({"origin": "motor_membrane",
                                   "simulated": True})
    assert result.category == "simulated_motor_action"


def test_motor_membrane_granted_by_default():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_MOTOR_MEMBRANE)


def test_mixed_sensory_gridworld_requires_approval():
    ps = PermissionSet.default()
    assert ps.requires_approval(PermissionScope.ENABLE_MIXED_SENSORY_GRIDWORLD)


def test_governance_allows_default_motor_membrane():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"motor_membrane": True}})
    assert decision.allowed


def test_governance_blocks_real_world_actuation_absolutely():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"motor_membrane": True}},
        {"real_world_actuation": True})
    assert not decision.allowed


def test_governance_blocks_firewall_disable():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"motor_membrane": True}},
        {"disable_firewall": True})
    assert not decision.allowed


def test_governance_mixed_needs_sensory_validation():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {
            "motor_membrane": True, "mixed_sensory_gridworld": True}})
    assert not decision.allowed


class _Runner:
    def __init__(self, motor):
        self.motor_membrane = motor


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_motor(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True, "profile_id": "gridworld_minimal",
        "real_world_authority": False, "action_count": 5,
        "simulated_action_count": 4, "veto_count": 1,
        "blocked_real_world_count": 0, "firewall_enabled": True,
        "firewall_can_be_disabled": False, "sandbox_health": "ok"})
    status = sup.motor_status()
    assert status["motor_membrane_enabled"] is True
    assert status["embodiment_profile"] == "gridworld_minimal"
    assert status["real_world_authority"] is False
    assert status["firewall_can_be_disabled"] is False


def test_ops_records_blocked_real_world_incident(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True, "blocked_real_world_count": 1,
                                "firewall_enabled": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "motor_real_world_action_attempt" in types


def test_ops_records_firewall_disabled_incident(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True, "firewall_enabled": False})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "motor_firewall_disable_attempt" in types


def test_ops_records_sandbox_corruption(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True, "firewall_enabled": True,
                                "sandbox_health": "corrupt"})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "motor_sandbox_corruption" in types
