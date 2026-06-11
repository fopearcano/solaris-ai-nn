"""Tests for governance over homeostasis."""

from __future__ import annotations

from solaris_ai_nn.governance import GovernancePolicy, PermissionScope
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_homeostasis_allowed_in_bounded_runs():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"homeostasis": True}))
    assert decision.allowed
    assert policy.permissions.allows(PermissionScope.ENABLE_HOMEOSTASIS)
    assert policy.permissions.allows(
        PermissionScope.ENABLE_NEED_DRIVEN_SUGGESTIONS)


def test_governance_blocks_unsafe_need_driven_suggestion():
    regulator = HomeostaticRegulator()
    result = regulator.update({
        "embodiment": {"energy": 0.8, "max_energy": 10.0,
                       "exhausted": True},
        "governance_blocks": {"rest": "operator paused all suggestions"},
    })
    blocked = {c.proposal: c for c in result.desire_candidates if c.blocked}
    assert "rest" in blocked
    assert blocked["rest"].governance_status == "blocked_by_governance"
    # The safety validator independently rejects real-world shapes.
    report = regulator.safety.validate_desire_candidate("motor_forward")
    assert not report.safe


def test_homeostasis_cannot_override_policy():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"homeostasis": True}),
        context={"needs_override_governance": True})
    assert not decision.allowed
    assert any(v.rule_id == "needs_never_override_governance"
               for v in decision.violations)
    # And the validator refuses override attempts outright.
    regulator = HomeostaticRegulator()
    assert not regulator.safety.validate_override_attempt(
        "governance").safe


def test_homeostasis_rules_in_policy_inventory():
    inventory = GovernancePolicy().to_dict()
    rule_ids = {r["rule_id"] for r in inventory["rules"]
                if r["category"] == "homeostasis"}
    assert {"homeostasis_allowed_bounded",
            "needs_never_override_governance", "needs_never_actuate",
            "shutdown_recommendation_via_ops",
            "no_anthropomorphic_claims"} <= rule_ids
