"""Tests for the localhost-only HTTP client (no service required)."""

from __future__ import annotations

from solaris_ai_nn.llm_adapter.base import LLMRequest, LLMTaskType
from solaris_ai_nn.llm_adapter.config import LLMAdapterConfig
from solaris_ai_nn.llm_adapter.local_client import LocalHTTPLLMAdapter


def _request():
    return LLMRequest(task_type=LLMTaskType.PARAPHRASE_RESPONSE,
                      input_text="steps=1", allowed_facts=["steps=1"])


def test_localhost_endpoint_validation():
    adapter = LocalHTTPLLMAdapter(config=LLMAdapterConfig(
        enabled=True, provider="ollama_compatible",
        endpoint_url="http://127.0.0.1:11434"))
    allowed, reason = adapter.endpoint_allowed()
    assert allowed
    assert "localhost" in reason


def test_remote_endpoint_blocked():
    adapter = LocalHTTPLLMAdapter(config=LLMAdapterConfig(
        enabled=True, provider="generic_local_http",
        endpoint_url="http://api.example.com/v1"))
    allowed, reason = adapter.endpoint_allowed()
    assert not allowed
    assert "not localhost" in reason
    response = adapter.generate(_request())
    assert response.refused
    assert "not localhost" in response.refusal_reason


def test_connection_error_falls_back_safely():
    # Port 9 (discard) on localhost: nothing is listening; the call must
    # refuse gracefully within the timeout, never raise.
    adapter = LocalHTTPLLMAdapter(config=LLMAdapterConfig(
        enabled=True, provider="ollama_compatible",
        endpoint_url="http://127.0.0.1:9", timeout_s=1.0))
    response = adapter.generate(_request())
    assert response.refused
    assert "unavailable" in response.refusal_reason
    assert adapter.status.refusals_total == 1


def test_no_external_service_required():
    adapter = LocalHTTPLLMAdapter(config=LLMAdapterConfig(
        enabled=True, provider="lmstudio_compatible"))
    response = adapter.generate(_request())
    assert response.refused  # no endpoint configured: honest refusal
    assert "no endpoint_url" in response.refusal_reason


def test_payload_shapes_per_provider():
    for provider, fragment in (("ollama_compatible", "/api/generate"),
                               ("lmstudio_compatible",
                                "/v1/chat/completions"),
                               ("generic_local_http", ":1234")):
        adapter = LocalHTTPLLMAdapter(config=LLMAdapterConfig(
            enabled=True, provider=provider,
            endpoint_url="http://127.0.0.1:1234"))
        url, payload = adapter._build_call("prompt", _request())
        assert fragment in url, provider
        assert "prompt" in str(payload) or "messages" in payload


def test_extract_text_variants():
    extract = LocalHTTPLLMAdapter._extract_text
    assert extract({"response": " ollama text "}) == "ollama text"
    assert extract({"choices": [{"message": {"content": "openai"}}]}) \
        == "openai"
    assert extract({"choices": [{"text": "completion"}]}) == "completion"
    assert extract({"output": "generic"}) == "generic"
    assert extract({"weird": True}) == ""
    assert extract("not a dict") == ""
