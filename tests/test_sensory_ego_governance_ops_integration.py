"""Sensory <-> Ego/Governance/Ops: read-only attribution, gating, status."""

from __future__ import annotations

from solaris_ai_nn.ego.ownership import OwnershipAttributor
from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_sensory_event_attributed_read_only():
    attr = OwnershipAttributor()
    result = attr.attribute_event({"origin": "read_only_environmental_input",
                                   "source_id": "j1"})
    assert result.category == "read_only_environmental_input"
    assert "operator" not in result.category


def test_real_sources_blocked_without_approval():
    ps = PermissionSet.default()
    assert not ps.allows(PermissionScope.ENABLE_REAL_READ_ONLY_SOURCES)
    assert ps.requires_approval(PermissionScope.ENABLE_REAL_READ_ONLY_SOURCES)


def test_governance_manifest_gates_real_sources():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {
            "sensory_membrane": True, "real_read_only_sources": True}})
    assert not decision.allowed
    assert PermissionScope.ENABLE_REAL_READ_ONLY_SOURCES \
        in decision.required_approvals


def test_governance_blocks_input_as_command():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"sensory_membrane": True}},
        {"input_as_command": True})
    assert not decision.allowed


def test_governance_allows_default_membrane():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"sensory_membrane": True}})
    assert decision.allowed


class _Runner:
    def __init__(self, membrane):
        self.sensory_membrane = membrane


def test_ops_status_includes_membrane(tmp_path):
    sup = OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))
    sup._last_runner = _Runner({
        "enabled": True, "source_count": 2, "healthy_source_count": 2,
        "degraded_source_count": 0, "events_per_minute": 3.0,
        "dropped_events": 0, "malformed_events": 0,
        "read_only_violation_count": 0})
    status = sup.membrane_status()
    assert status["sensory_membrane_enabled"] is True
    assert status["source_count"] == 2


def test_ops_records_read_only_violation(tmp_path):
    sup = OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))
    sup._last_runner = _Runner({"enabled": True,
                                "read_only_violation_count": 1})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "health_critical" in types
