"""Tests for governance and ops supervision over the ego layer."""

from __future__ import annotations

import inspect

from solaris_ai_nn.governance import GovernancePolicy, PermissionScope
from solaris_ai_nn.ops import incident as I
from solaris_ai_nn.ops.incident import IncidentLog
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_ego_allowed_in_bounded_runs():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(_manifest_view({"ego": True}))
    assert decision.allowed
    assert policy.permissions.allows(PermissionScope.ENABLE_EGO_MODEL)
    assert policy.permissions.allows(
        PermissionScope.ENABLE_DIMENSIONAL_COMPARISON)
    assert policy.permissions.allows(PermissionScope.ENABLE_SELF_REPORT)


def test_self_model_cannot_grant_permissions_policy():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"ego": True}),
        context={"self_model_grants_permissions": True})
    assert not decision.allowed
    assert any(v.rule_id == "self_model_cannot_grant_permissions"
               for v in decision.violations)


def test_ego_rules_in_policy_inventory():
    inventory = GovernancePolicy().to_dict()
    rule_ids = {r["rule_id"] for r in inventory["rules"]
                if r["category"] == "ego"}
    assert {"ego_model_allowed_bounded", "self_report_claim_guard",
            "self_model_cannot_grant_permissions",
            "boundary_violations_audited",
            "identity_claims_scanned"} <= rule_ids


def test_ego_incident_types_registered():
    for incident_type in (I.EGO_BOUNDARY_VIOLATION,
                          I.IDENTITY_ANCHOR_MISMATCH,
                          I.PERSPECTIVE_STUCK, I.ATTRIBUTION_CONFLICT,
                          I.SUGGESTION_COMMITTED_MISMATCH,
                          I.COUNTERFACTUAL_BOUNDARY_LEAK):
        assert incident_type in I.INCIDENT_TYPES


def test_boundary_violation_logged_as_incident(tmp_path):
    log = IncidentLog(tmp_path / "incidents.jsonl")
    log.record(I.EGO_BOUNDARY_VIOLATION, "warning",
               "1 ego boundary violation recorded",
               related_metric="boundary_violations")
    rows = log.list_incidents()
    assert rows and rows[-1]["type"] == "ego_boundary_violation"


def test_ego_monitoring_never_requests_shutdown():
    source = inspect.getsource(OperationalSupervisor._supervise)
    block = source.split("Ego/self-model monitoring")[1].split(
        "budget_report")[0]
    assert "request_shutdown" not in block
    assert "_stop_requested" not in block


def test_identity_mismatch_detected_by_health_monitor(tmp_path):
    manifest = OperationalRunManifest(
        mode="bounded", max_steps=60, healthcheck_interval_steps=20,
        state_dir=str(tmp_path / "state"),
        artifact_dir=str(tmp_path / "ops"), seed=5,
        enabled_features={"ego": True})
    sup = OperationalSupervisor(
        manifest=manifest,
        registry=RunRegistry(tmp_path / "registry.json"),
        governance_dir=str(tmp_path / "gov"))
    original = sup._supervise

    def wrapped(*args, **kw):
        runner = sup._last_runner
        if runner is not None and runner.ego is not None:
            runner.ego.identity.identity_warnings = [
                "identity anchor 'run_id' mismatches the previous value"]
        original(*args, **kw)

    sup._supervise = wrapped
    status = sup.run()
    types = [i["type"] for i in status["incidents"]]
    assert "identity_anchor_mismatch" in types
    # The run still completed its bound: evidence only, no stop.
    assert (status["telemetry"] or {}).get("lifetime_steps") == 60
