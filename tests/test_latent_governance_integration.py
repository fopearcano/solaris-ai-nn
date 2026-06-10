"""Tests for governance over latent cognition."""

from __future__ import annotations

from solaris_ai_nn.governance import (
    ApprovalRegistry,
    GovernancePolicy,
    PermissionScope,
)
from solaris_ai_nn.latent.safety import LatentSafetyValidator


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_latent_dry_run_allowed():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(_manifest_view({"latent": True}))
    assert decision.allowed
    # The permission scopes exist and default sensibly.
    assert policy.permissions.allows(PermissionScope.ENABLE_LATENT)
    assert policy.permissions.allows(PermissionScope.ENABLE_LATENT_DRY_RUN)
    assert policy.permissions.allows(PermissionScope.RUN_DREAM_CYCLE)
    assert policy.permissions.allows(
        PermissionScope.RUN_COUNTERFACTUAL_REPLAY)


def test_latent_plasticity_blocked_without_approval():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(_manifest_view(
        {"latent": True, "latent_plasticity": True}))
    assert not decision.allowed
    assert PermissionScope.ENABLE_LATENT_PLASTICITY \
        in decision.required_approvals

    registry = ApprovalRegistry()
    request = registry.request_approval(
        PermissionScope.ENABLE_LATENT_PLASTICITY,
        reason="bounded latent learning experiment")
    registry.approve(request.request_id, "tester")
    approved = GovernancePolicy(approvals=registry)
    assert approved.evaluate_manifest(_manifest_view(
        {"latent": True, "latent_plasticity": True})).allowed


def test_latent_forbidden_while_sidecar_publishing():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"latent": True, "sidecar": True}),
        context={"sidecar_publish": True})
    assert not decision.allowed
    assert any(v.rule_id == "latent_forbidden_while_publishing"
               for v in decision.violations)


def test_counterfactual_leak_blocked():
    """Counterfactual data posing as a real observation is rejected."""
    validator = LatentSafetyValidator()
    leak = {"kind": "invert_valence", "simulated": True, "offline": True,
            "real_observation": True, "rows": []}
    assert not validator.validate_counterfactual(leak).safe
    unlabelled = {"kind": "invert_valence", "rows": []}
    assert not validator.validate_counterfactual(unlabelled).safe
    publishing = {"kind": "x", "simulated": True, "offline": True,
                  "publish": True, "rows": []}
    assert not validator.validate_counterfactual(publishing).safe


def test_latent_rules_in_policy_inventory():
    inventory = GovernancePolicy().to_dict()
    latent_rules = [r for r in inventory["rules"]
                    if r["category"] == "latent"]
    rule_ids = {r["rule_id"] for r in latent_rules}
    assert {"latent_dry_run_allowed", "latent_mutation_requires_approval",
            "latent_forbidden_while_publishing",
            "counterfactuals_are_not_observations",
            "latent_loops_bounded"} <= rule_ids


def test_pilot_readiness_gates_latent_plasticity(tmp_path):
    from solaris_ai_nn.pilot.pilot_manifest import PilotManifest
    from solaris_ai_nn.pilot.readiness import PilotReadinessCheck

    manifest = PilotManifest(profile="simulated", operator="tester",
                             state_dir=str(tmp_path / "state"),
                             artifact_dir=str(tmp_path / "pilots"),
                             max_steps=50, notes="latent pilot")
    manifest.enabled_features["latent"] = True
    manifest.enabled_features["latent_plasticity"] = True
    report = PilotReadinessCheck(manifest=manifest,
                                 governance=GovernancePolicy()).run(
        {"approved_output_roots": [str(tmp_path)],
         "quick_suite_passed": "skipped", "restart_demo_passed": "skipped"})
    assert not report.ready
    assert any("latent" in i.detail for i in report.blocking_issues())
