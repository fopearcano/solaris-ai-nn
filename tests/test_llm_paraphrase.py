"""Tests for the paraphrase-or-fallback layer."""

from __future__ import annotations

from solaris_ai_nn.communication.response_builder import ResponseBuilder
from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter
from solaris_ai_nn.llm_adapter.paraphrase import LLMParaphraser


def _response():
    return ResponseBuilder().status_response("steps=42; health=ok",
                                             ["field:steps"])


def test_safe_paraphrase_accepted():
    paraphraser = LLMParaphraser(adapter=MockLLMAdapter())
    response = _response()
    out = paraphraser.paraphrase_response(response)
    assert out.text.startswith("In plain terms:")
    assert "steps=42" in out.text
    assert out.metadata["llm_paraphrased"] is True
    assert paraphraser.accepted_count == 1
    # The paraphrase declares itself in the limitations.
    assert any("LLM paraphrase" in lim for lim in out.limitations)


def test_unsafe_paraphrase_rejected():
    paraphraser = LLMParaphraser(
        adapter=MockLLMAdapter(force_unsafe_output=True))
    response = _response()
    original = response.text
    out = paraphraser.paraphrase_response(response)
    assert out.text == original  # untouched
    assert not out.metadata.get("llm_paraphrased")
    assert paraphraser.rejected_count == 1
    assert paraphraser.fallback_count == 1
    assert paraphraser.validator.failures_total == 1


def test_fallback_returns_deterministic_original():
    paraphraser = LLMParaphraser(
        adapter=MockLLMAdapter(force_refusal=True))
    response = _response()
    original = response.text
    out = paraphraser.paraphrase_response(response)
    assert out.text == original
    assert paraphraser.fallback_count == 1
    assert paraphraser.accepted_count == 0


def test_paraphrase_explanation_and_section():
    paraphraser = LLMParaphraser(adapter=MockLLMAdapter())
    explanation = paraphraser.paraphrase_explanation(
        "the arbitrator selected rest because energy pressure was high")
    assert "rest" in explanation
    section = paraphraser.paraphrase_report_section(
        "# Heading\n\nvalue: 7\n")
    assert "value: 7" in section


def test_evidence_refs_must_survive():
    paraphraser = LLMParaphraser(adapter=MockLLMAdapter())
    response = _response()
    out = paraphraser.paraphrase_response(response)
    # The mock keeps the whole text, so the required ref is present; the
    # validator enforced it via metadata.required_refs.
    assert "field:steps" in out.text
