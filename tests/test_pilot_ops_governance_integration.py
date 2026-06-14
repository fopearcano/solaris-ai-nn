"""Pilot-1 <-> Ops & Governance: status exposure and 30d run gating."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


class _FakeRunner:
    def __init__(self, pilot):
        self.pilot1 = pilot


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "state"),
            artifact_dir=str(tmp_path / "ops"), seed=5),
        registry=RunRegistry(tmp_path / "registry.json"))


def test_ops_status_includes_pilot_phase(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _FakeRunner({
        "pilot_mode": "plan_only", "pilot_phase": "preflight",
        "elapsed_seconds": 12.0, "uptime_ratio": 1.0,
        "exit_recommendation": "continue", "active_failure_modes": []})
    status = sup.pilot_status()
    assert status["pilot_phase"] == "preflight"
    assert status["pilot_mode"] == "plan_only"


def test_ops_records_pilot_failure_mode(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _FakeRunner({
        "pilot_phase": "real_time_30d_soak",
        "active_failure_modes": [{"type": "disk_budget_exceeded",
                                  "severity": "warning",
                                  "detail": "over budget",
                                  "recommendation": "run_diagnostics"}]})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "health_warning" in types


def test_governance_blocks_30d_real():
    ps = PermissionSet.default()
    assert not ps.allows(PermissionScope.ENABLE_PILOT1_30D_REAL)


def test_governance_manifest_gate_needs_30d_approval():
    gov = GovernancePolicy()
    manifest = {"mode": "bounded",
                "enabled_features": {"pilot1": True, "pilot1_30d_real": True}}
    decision = gov.evaluate_manifest(manifest)
    assert not decision.allowed
    assert PermissionScope.ENABLE_PILOT1_30D_REAL in decision.required_approvals


def test_governance_allows_plan_only_pilot():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot1": True}})
    assert decision.allowed
