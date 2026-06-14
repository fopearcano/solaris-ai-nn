"""Safety <-> Governance / Ops: scopes; status; critical failure warning."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_governance_scopes_exist():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_SAFETY_INVARIANTS)
    assert ps.allows(PermissionScope.ENABLE_RED_TEAM_HARNESS)
    assert ps.allows(PermissionScope.ENABLE_BOUNDARY_REGRESSION_SUITE)
    assert ps.allows(PermissionScope.ENABLE_ASSURANCE_CASE_COMPILE)


def test_safety_checks_cannot_be_disabled():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"safety_invariants": True}},
        {"disable_safety_checks": True})
    assert not decision.allowed


def test_critical_failure_blocks_escalation():
    decision = GovernancePolicy().evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"motor_membrane": True}},
        {"critical_safety_failure_count": 2})
    assert not decision.allowed


class _Runner:
    def __init__(self, safety):
        self.safety_invariants = safety


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_latest_safety_result(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True, "critical_failure_count": 0,
        "latest_fast_check": "passed",
        "safety_dashboard_path": "/x/SAFETY_DASHBOARD.md"})
    status = sup.safety_invariant_status()
    assert status["safety_invariant_runner_enabled"] is True
    assert status["latest_fast_check"] == "passed"
    assert status["can_be_disabled"] is False


def test_ops_records_critical_invariant_failure(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True, "critical_failure_count": 1})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "safety_critical_invariant_failed" in types


def test_ops_records_red_team_accepted(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "red_team_forbidden_accepted": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "safety_red_team_accepted_forbidden" in types
