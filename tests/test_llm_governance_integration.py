"""Tests for governance over the LLM adapter."""

from __future__ import annotations

from solaris_ai_nn.governance import GovernancePolicy, PermissionScope
from solaris_ai_nn.llm_adapter.config import LLMAdapterConfig
from solaris_ai_nn.llm_adapter.safety import LLMAdapterSafetyValidator


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_local_llm_requires_permission_and_config():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"llm_adapter": True}))
    assert decision.allowed  # scope granted, config still off by default
    assert policy.permissions.allows(
        PermissionScope.ENABLE_LOCAL_LLM_ADAPTER)
    assert LLMAdapterConfig().enabled is False  # config gate independent


def test_remote_endpoint_prohibited():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"llm_adapter": True}),
        context={"llm_endpoint_remote": True})
    assert not decision.allowed
    assert any(v.rule_id == "llm_remote_prohibited"
               for v in decision.violations)
    assert policy.permissions.requires_approval(
        PermissionScope.ALLOW_REMOTE_LLM_ENDPOINT)
    # The endpoint validator enforces the same thing without governance.
    validator = LLMAdapterSafetyValidator()
    config = LLMAdapterConfig(enabled=True,
                              provider="generic_local_http",
                              endpoint_url="https://api.example.com")
    assert not validator.validate_endpoint(config, policy).safe


def test_llm_cannot_approve_requests():
    from solaris_ai_nn.governance.approval import ApprovalRegistry
    from solaris_ai_nn.llm_adapter.base import LLMResponse

    registry = ApprovalRegistry()
    request = registry.request_approval("enable_sidecar_suggestions",
                                        reason="test")
    validator = LLMAdapterSafetyValidator()
    llm_output = LLMResponse(
        output_text=f"Request approved: {request.request_id}")
    assert not validator.validate_response(llm_output).safe
    # The registry never saw an LLM: the request is still pending.
    assert registry.requests[request.request_id].status == "pending"
    rules = {r["rule_id"] for r in GovernancePolicy().to_dict()["rules"]
             if r["category"] == "llm"}
    assert {"llm_translator_only", "llm_cannot_approve",
            "llm_cannot_unsafe_to_safe", "llm_output_validated",
            "llm_usage_audited", "llm_remote_prohibited"} <= rules
