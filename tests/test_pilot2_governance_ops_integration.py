"""Pilot-2 <-> Governance / Ops: real soak gated; ops status includes Pilot-2."""

from __future__ import annotations

from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_real_soak_gated_by_default():
    ps = PermissionSet.default()
    for scope in (PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_24H,
                  PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_7D,
                  PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_30D):
        assert not ps.allows(scope)
        assert ps.requires_approval(scope)


def test_governance_blocks_real_soak():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {
            "pilot2": True, "pilot2_real_30d": True}})
    assert not decision.allowed
    assert PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_30D \
        in decision.required_approvals


def test_governance_blocks_input_as_command():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot2": True}},
        {"input_as_command": True})
    assert not decision.allowed


def test_governance_allows_default_pilot2():
    gov = GovernancePolicy()
    decision = gov.evaluate_manifest(
        {"mode": "bounded", "enabled_features": {"pilot2": True}})
    assert decision.allowed


class _Runner:
    def __init__(self, pilot2):
        self.pilot2 = pilot2


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10, state_dir=str(tmp_path / "s"),
            artifact_dir=str(tmp_path / "o"), seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_ops_status_includes_pilot2(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({
        "enabled": True, "pilot2_phase": "fixture_short_run",
        "source_count": 2, "reliable_source_count": 2,
        "unsafe_source_count": 0,
        "source_reliability_summary": {"reliable": 2},
        "recommendation": "continue"})
    status = sup.pilot2_status()
    assert status["pilot2_enabled"] is True
    assert status["pilot2_phase"] == "fixture_short_run"


def test_ops_records_unsafe_source_warning(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True, "unsafe_source_count": 1})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert "health_critical" in types
