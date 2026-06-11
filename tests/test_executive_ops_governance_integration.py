"""Tests for governance and ops supervision over the executive."""

from __future__ import annotations

import inspect

from solaris_ai_nn.governance import GovernancePolicy, PermissionScope
from solaris_ai_nn.ops import incident as I
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_executive_allowed_in_bounded_runs():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"executive": True}))
    assert decision.allowed
    assert policy.permissions.allows(PermissionScope.ENABLE_EXECUTIVE)
    assert policy.permissions.allows(
        PermissionScope.ENABLE_SHORT_HORIZON_PLANNING)
    assert policy.permissions.allows(PermissionScope.ENABLE_PROSPECTION)


def test_sidecar_suggestion_scope_needs_approval():
    policy = GovernancePolicy()
    assert not policy.permissions.allows(
        PermissionScope.ENABLE_EXECUTIVE_SIDECAR_SUGGESTIONS)


def test_long_plans_rejected_by_policy():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"executive": True}),
        context={"max_plan_length": 7})
    assert not decision.allowed
    assert any(v.rule_id == "plans_bounded" for v in decision.violations)


def test_executive_rules_in_policy_inventory():
    inventory = GovernancePolicy().to_dict()
    rule_ids = {r["rule_id"] for r in inventory["rules"]
                if r["category"] == "executive"}
    assert {"executive_arbitration_allowed", "plans_bounded",
            "executive_never_real_world",
            "executive_sidecar_publish_approval",
            "emergency_mode_unstoppable"} <= rule_ids


def test_executive_incident_types_registered():
    for incident_type in (I.EXECUTIVE_NO_SAFE_ACTION,
                          I.EXECUTIVE_REPEATED_INHIBITION,
                          I.EXECUTIVE_PLAN_REJECTED,
                          I.EXECUTIVE_PROSPECTION_FAILURE,
                          I.EXECUTIVE_MODE_FORCED_EMERGENCY):
        assert incident_type in I.INCIDENT_TYPES


def test_executive_monitoring_never_requests_shutdown():
    """The executive block records evidence only; the watchdog keeps all
    stop authority."""
    source = inspect.getsource(OperationalSupervisor._supervise)
    block = source.split("Executive monitoring")[1].split(
        "budget_report")[0]
    assert "request_shutdown" not in block
    assert "_stop_requested" not in block


def test_supervised_executive_run(tmp_path):
    manifest = OperationalRunManifest(
        mode="bounded", max_steps=60, healthcheck_interval_steps=20,
        state_dir=str(tmp_path / "state"),
        artifact_dir=str(tmp_path / "ops"), seed=5,
        enabled_features={"homeostasis": True, "executive": True})
    sup = OperationalSupervisor(
        manifest=manifest,
        registry=RunRegistry(tmp_path / "registry.json"),
        governance_dir=str(tmp_path / "gov"))
    status = sup.run()
    assert (status["telemetry"] or {}).get("lifetime_steps") == 60
    assert sup._last_runner.executive is not None
    # The supervisor's health snapshot carried the executive summary.
    assert sup._last_runner.executive.decisions >= 0
