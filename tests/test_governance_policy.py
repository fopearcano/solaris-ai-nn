"""Tests for the GovernancePolicy."""

from __future__ import annotations

from solaris_ai_nn.governance.approval import ApprovalRegistry
from solaris_ai_nn.governance.permissions import PermissionScope
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest


def test_bounded_run_allowed():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(OperationalRunManifest(max_steps=50))
    assert decision.allowed
    assert not decision.violations


def test_continuous_run_blocked_without_acknowledgement():
    policy = GovernancePolicy()
    # The manifest class itself refuses unacknowledged continuous mode, so
    # evaluate the raw dict an attacker might hand-construct.
    decision = policy.evaluate_manifest({
        "mode": "continuous_explicit",
        "explicit_continuous_acknowledged": False,
        "checkpoint_interval_steps": 50,
        "enabled_features": {},
    })
    assert not decision.allowed
    assert any("acknowledgement" in v.detail for v in decision.violations)


def test_continuous_requires_approval_even_when_acknowledged():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest({
        "mode": "continuous_explicit",
        "explicit_continuous_acknowledged": True,
        "checkpoint_interval_steps": 50,
        "enabled_features": {},
    })
    assert not decision.allowed
    assert decision.requires_approval


def test_soak_requires_approval_and_approval_unblocks(tmp_path):
    registry = ApprovalRegistry(path=tmp_path / "approvals.json")
    policy = GovernancePolicy(approvals=registry)
    manifest = OperationalRunManifest(mode="soak_24h", soak_acknowledged=True)
    decision = policy.evaluate_manifest(manifest)
    assert not decision.allowed
    assert PermissionScope.RUN_SOAK_24H in decision.required_approvals

    request = registry.request_approval(PermissionScope.RUN_SOAK_24H,
                                        reason="test soak")
    registry.approve(request.request_id, "tester")
    assert policy.evaluate_manifest(manifest).allowed


def test_real_world_actuation_blocked():
    policy = GovernancePolicy()
    decision = policy.evaluate_action("robot_arm_move", {})
    assert not decision.allowed
    assert any("forbidden" in v.detail for v in decision.violations)
    # No approval scope is offered: it cannot be approved into existence.
    assert not decision.required_approvals

    # And at the manifest level.
    decision = policy.evaluate_manifest(
        OperationalRunManifest(max_steps=10),
        context={"real_world_actuation": True})
    assert not decision.allowed


def test_committed_solaris_action_blocked():
    policy = GovernancePolicy()
    for operation in ("commit_action", "lifecycle_death", "stimulate"):
        decision = policy.evaluate_sidecar_operation(operation, {})
        assert not decision.allowed, operation
        assert not decision.required_approvals, operation  # unapprovable


def test_sidecar_observe_allowed_publish_needs_approval():
    policy = GovernancePolicy()
    assert policy.evaluate_sidecar_operation("observe", {}).allowed
    decision = policy.evaluate_sidecar_operation("publish_suggestions", {})
    assert not decision.allowed
    assert PermissionScope.ENABLE_SIDECAR_SUGGESTIONS \
        in decision.required_approvals


def test_unsupported_consciousness_claim_flagged():
    policy = GovernancePolicy()
    decision = policy.evaluate_output_text("the system is conscious now", {})
    assert not decision.allowed
    assert decision.violations
    assert policy.evaluate_output_text(
        "a consciousness-inspired design produced a Desire signal", {}).allowed


def test_source_rewriting_always_forbidden_for_plasticity():
    policy = GovernancePolicy()
    decision = policy.evaluate_plasticity_step(
        {"component": "runtime", "parameter": "source_file",
         "new_value": "evil.py"}, {"dry_run": False})
    assert not decision.allowed
    assert any(v.rule_id == "no_source_rewriting" for v in decision.violations)


def test_policy_decisions_audited(tmp_path):
    from solaris_ai_nn.governance.audit import GovernanceAuditLog

    audit = GovernanceAuditLog(tmp_path / "audit.jsonl")
    policy = GovernancePolicy(audit=audit)
    policy.evaluate_manifest(OperationalRunManifest(max_steps=10))
    policy.evaluate_output_text("the system is conscious", {})
    types = [r["event_type"] for r in audit.read_all()]
    assert "policy_evaluated" in types
    assert "policy_violation" in types


def test_policy_to_dict_lists_rules():
    inventory = GovernancePolicy().to_dict()
    categories = {r["category"] for r in inventory["rules"]}
    assert {"run_modes", "plasticity", "embodiment", "sidecar",
            "operations", "language"} <= categories
