"""Research <-> Governance / Ops: scopes; status; warnings."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_governance_scopes_exist():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_RESEARCH_LAB)
    assert ps.allows(PermissionScope.ENABLE_RESEARCH_ABLATION)
    assert ps.allows(PermissionScope.ENABLE_RESEARCH_BASELINES)
    assert ps.allows(PermissionScope.ENABLE_RESEARCH_NULL_MODELS)
    assert ps.allows(PermissionScope.ENABLE_RESEARCH_REPORT)


def test_default_research_allowed():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"research_lab": True}})
    assert decision.allowed


def test_external_authority_blocked():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"research_lab": True}},
        {"external_authority": True})
    assert not decision.allowed


def test_ablating_hard_safety_blocked():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"research_lab": True}},
        {"ablate_safety_invariants": True})
    assert not decision.allowed


def test_deleting_results_blocked():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"research_lab": True}},
        {"delete_unfavorable_results": True})
    assert not decision.allowed


class _Runner:
    def __init__(self, research):
        self.research_lab = research


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_current_experiment(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True, "current_experiment_id": "EXP_1",
        "current_variant": "full",
        "latest_research_report_path": "/x/RESEARCH_REPORT.md"})
    status = sup.research_lab_status()
    assert status["research_lab_enabled"] is True
    assert status["current_experiment_id"] == "EXP_1"
    assert status["current_variant"] == "full"


def test_ops_records_critical_safety_failure(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "critical_safety_failure_count": 1})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "research_critical_safety_failed" in types


def test_ops_records_missing_baseline(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True, "missing_baseline": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "research_missing_baseline" in types
