"""Tests for the LLM adapter configuration."""

from __future__ import annotations

from solaris_ai_nn.llm_adapter.config import (
    LLMAdapterConfig,
    is_localhost_url,
)


def test_disabled_by_default():
    config = LLMAdapterConfig()
    assert config.enabled is False
    assert config.allow_remote_network is False
    assert config.allow_network_localhost_only is True
    assert config.fallback_to_deterministic is True
    assert config.require_grounding_validation is True
    assert config.require_claim_guard is True
    assert config.validate() == []  # disabled is always valid


def test_localhost_allowed_when_configured():
    for url in ("http://127.0.0.1:11434", "http://localhost:1234",
                "http://[::1]:8080"):
        assert is_localhost_url(url), url
        config = LLMAdapterConfig(enabled=True,
                                  provider="ollama_compatible",
                                  endpoint_url=url)
        assert config.validate() == [], url
        assert config.endpoint_is_localhost()


def test_remote_endpoint_rejected_by_default():
    config = LLMAdapterConfig(enabled=True, provider="generic_local_http",
                              endpoint_url="http://api.example.com")
    issues = config.validate()
    assert issues
    assert "not localhost" in issues[0]
    # Even with allow_remote_network, the localhost-only flag must also
    # be flipped (and governance must approve on top of that).
    still = LLMAdapterConfig(enabled=True, provider="generic_local_http",
                             endpoint_url="http://api.example.com",
                             allow_remote_network=True)
    assert any("governance" in issue for issue in still.validate())


def test_safety_levers_cannot_be_disabled():
    config = LLMAdapterConfig(enabled=True,
                              fallback_to_deterministic=False,
                              require_claim_guard=False,
                              require_grounding_validation=False)
    issues = " ".join(config.validate())
    assert "fallback_to_deterministic" in issues
    assert "require_claim_guard" in issues
    assert "require_grounding_validation" in issues


def test_unknown_provider_rejected():
    import pytest

    with pytest.raises(ValueError):
        LLMAdapterConfig(provider="openai_cloud")
