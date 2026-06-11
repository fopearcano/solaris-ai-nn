"""Tests for the LLM adapter base interfaces."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.llm_adapter.base import (
    DEFAULT_FORBIDDEN_CLAIMS,
    LLMAdapter,
    LLMRequest,
    LLMResponse,
    LLMTaskType,
)


def test_request_serializes():
    request = LLMRequest(task_type=LLMTaskType.PARAPHRASE_RESPONSE,
                         input_text="Status summary: steps=5.",
                         allowed_facts=["steps=5"],
                         grounded_context={"source": "ops"})
    data = request.to_dict()
    json.dumps(data, default=str)
    for key in ("request_id", "task_type", "input_text",
                "grounded_context", "allowed_facts", "forbidden_claims",
                "max_tokens", "temperature", "created_at", "metadata"):
        assert key in data, key
    # The default forbidden claims always ride along.
    for claim in DEFAULT_FORBIDDEN_CLAIMS:
        assert claim in request.forbidden_claims
    with pytest.raises(ValueError):
        LLMRequest(task_type="mind_control")


def test_response_serializes():
    response = LLMResponse(request_id="abc", output_text="text",
                           used_context_refs=["context:ops"])
    data = response.to_dict()
    json.dumps(data, default=str)
    for key in ("response_id", "request_id", "output_text",
                "used_context_refs", "refused", "refusal_reason",
                "safety_status", "claim_guard_status", "raw_model_name",
                "metadata"):
        assert key in data, key
    assert data["safety_status"] == "unvalidated"
    assert data["claim_guard_status"] == "unchecked"


def test_task_types_exist():
    assert len(LLMTaskType.ALL) == 8
    for task in ("paraphrase_response", "summarize_report",
                 "summarize_trace", "classification_assist",
                 "explain_metrics", "operator_friendly_status",
                 "report_polish", "claim_rewrite"):
        assert task in LLMTaskType.ALL, task


def test_adapter_has_no_authority_surface():
    assert LLMAdapter.can_execute_tools() is False
    assert LLMAdapter.can_call_functions() is False
    assert LLMAdapter.can_modify_state() is False
    assert LLMAdapter.is_authority() is False


def test_adapter_errors_become_refusals():
    class ExplodingAdapter(LLMAdapter):
        name = "exploding"

        def _generate(self, request):
            raise RuntimeError("boom")

    adapter = ExplodingAdapter()
    response = adapter.generate(LLMRequest(
        task_type=LLMTaskType.PARAPHRASE_RESPONSE, input_text="x"))
    assert response.refused
    assert "adapter error" in response.refusal_reason
    assert adapter.status.errors_total == 1
