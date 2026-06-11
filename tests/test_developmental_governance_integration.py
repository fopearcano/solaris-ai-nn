"""Tests for governance over the developmental runtime."""

from __future__ import annotations

import pytest

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.governance import GovernancePolicy, PermissionScope


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_short_simulated_run_allowed():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"developmental": True}))
    assert decision.allowed
    assert policy.permissions.allows(
        PermissionScope.ENABLE_DEVELOPMENTAL_RUNTIME)


def test_month_year_scale_requires_approval(tmp_path):
    policy = GovernancePolicy()
    month = policy.evaluate_manifest(
        _manifest_view({"developmental": True}),
        context={"month_scale": True})
    assert not month.allowed
    year = policy.evaluate_manifest(
        _manifest_view({"developmental": True}),
        context={"year_scale": True})
    assert not year.allowed
    # The runtime itself enforces the same gate.
    with pytest.raises(PermissionError):
        DevelopmentalRuntime(state_dir=tmp_path / "m",
                             enable_month_scale=True, max_steps=10,
                             governance=policy).run()


def test_fossil_memory_permission_checked():
    policy = GovernancePolicy()
    assert policy.permissions.allows(
        PermissionScope.ENABLE_FOSSIL_MEMORY)
    assert policy.permissions.allows(
        PermissionScope.ENABLE_MEMORY_COMPRESSION)
    assert policy.permissions.requires_approval(
        PermissionScope.ENABLE_DEVELOPMENTAL_PRUNING)


def test_developmental_rules_in_policy_inventory():
    rules = {r["rule_id"] for r in GovernancePolicy().to_dict()["rules"]
             if r["category"] == "developmental"}
    assert {"developmental_simulated_allowed",
            "month_year_scale_approval",
            "compression_preserves_evidence",
            "developmental_pruning_approval",
            "autobiography_claim_guard",
            "no_teacher_loop_required"} <= rules
