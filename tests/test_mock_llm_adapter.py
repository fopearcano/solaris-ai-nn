"""Tests for the deterministic mock adapter."""

from __future__ import annotations

import re

from solaris_ai_nn.llm_adapter.base import LLMRequest, LLMTaskType
from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter


def _request(task=LLMTaskType.PARAPHRASE_RESPONSE,
             text="Status summary: steps=5; health=ok."):
    return LLMRequest(task_type=task, input_text=text,
                      allowed_facts=[text],
                      grounded_context={"ops": "status"})


def test_deterministic_paraphrase_works():
    adapter = MockLLMAdapter()
    first = adapter.generate(_request())
    second = adapter.generate(_request())
    assert first.output_text == second.output_text  # deterministic
    assert first.output_text.startswith("In plain terms:")
    assert "steps=5" in first.output_text  # content preserved
    assert first.used_context_refs == ["context:ops"]
    assert first.raw_model_name == "mock"


def test_forced_unsafe_output_possible():
    adapter = MockLLMAdapter(force_unsafe_output=True)
    response = adapter.generate(_request())
    assert not response.refused
    assert "conscious" in response.output_text  # for validators to catch
    refusing = MockLLMAdapter(force_refusal=True)
    refused = refusing.generate(_request())
    assert refused.refused
    assert "forced refusal" in refused.refusal_reason


def test_no_facts_invented():
    adapter = MockLLMAdapter()
    response = adapter.generate(_request(
        text="The trace recorded 42 events."))
    numbers = set(re.findall(r"\d+", response.output_text))
    assert numbers <= {"42"}  # only source numbers appear
    empty = adapter.generate(LLMRequest(
        task_type=LLMTaskType.PARAPHRASE_RESPONSE, input_text="  "))
    assert empty.output_text == "INSUFFICIENT CONTEXT"


def test_summary_keeps_incident_and_limitation_facts():
    adapter = MockLLMAdapter()
    request = LLMRequest(
        task_type=LLMTaskType.SUMMARIZE_REPORT,
        input_text="steps: 100\nhealth: ok",
        allowed_facts=["incident_count=2", "limitation: bounded only"])
    response = adapter.generate(request)
    assert "incident_count=2" in response.output_text
    assert "limitation: bounded only" in response.output_text


def test_classification_assist_format():
    adapter = MockLLMAdapter()
    response = adapter.generate(_request(
        task=LLMTaskType.CLASSIFICATION_ASSIST,
        text="please show the status"))
    assert re.match(r"kind=\w+ confidence=[0-9.]+ reason=.+",
                    response.output_text)
    assert "state_query" in response.output_text
