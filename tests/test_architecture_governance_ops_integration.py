"""Architecture <-> Governance / Ops: scopes; status; warnings."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_governance_scopes_exist():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_ARCHITECTURE_EVOLUTION)
    assert ps.allows(PermissionScope.ENABLE_ARCHITECTURE_REVIEW)
    assert ps.allows(PermissionScope.ENABLE_ARCHITECTURE_ROADMAP_COMPILE)
    assert ps.allows(PermissionScope.ENABLE_ARCHITECTURE_PRUNING_PROPOSALS)
    assert ps.allows(PermissionScope.ENABLE_ARCHITECTURE_ADR_GENERATION)


def test_default_architecture_allowed():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded",
         "enabled_features": {"architecture_evolution": True}})
    assert decision.allowed


def test_source_change_blocked():
    for ctx in ({"apply_source_change": True}, {"auto_delete_module": True},
                {"run_git": True}, {"prune_safety_critical": True},
                {"real_world_actuation": True}):
        decision = GovernancePolicy().evaluate_manifest(
            {"mode": "bounded",
             "enabled_features": {"architecture_evolution": True}}, ctx)
        assert not decision.allowed, ctx


class _Runner:
    def __init__(self, arch):
        self.architecture_evolution = arch


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_architecture_review(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True,
        "latest_architecture_review_path": "/x/ARCHITECTURE_REVIEW.md",
        "open_adr_count": 2, "pruning_proposal_count": 1})
    status = sup.architecture_status()
    assert status["architecture_evolution_enabled"] is True
    assert status["latest_architecture_review_path"] == \
        "/x/ARCHITECTURE_REVIEW.md"
    assert status["modifies_source_code"] is False


def test_ops_records_safety_critical_pruning_attempt(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "proposed_safety_critical_pruning": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "architecture_safety_critical_pruning" in types


def test_ops_records_roadmap_forbidden_action(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "roadmap_forbidden_action": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "architecture_roadmap_forbidden_action" in types
