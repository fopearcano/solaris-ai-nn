"""Tests for the grounding validator."""

from __future__ import annotations

from solaris_ai_nn.llm_adapter.base import LLMRequest, LLMResponse, LLMTaskType
from solaris_ai_nn.llm_adapter.grounding import GroundingValidator


def _pair(facts, output, input_text="", metadata=None):
    request = LLMRequest(task_type=LLMTaskType.PARAPHRASE_RESPONSE,
                         input_text=input_text or " ".join(facts),
                         allowed_facts=list(facts),
                         metadata=metadata or {})
    response = LLMResponse(request_id=request.request_id,
                           output_text=output)
    return request, response


def test_grounded_output_passes():
    validator = GroundingValidator()
    request, response = _pair(
        ["steps=42", "health=ok"],
        "In plain terms: the run recorded steps=42 with health=ok.")
    report = validator.validate(request, response)
    assert report.passed
    assert "number_provenance" in report.checks_run


def test_invented_fact_fails():
    validator = GroundingValidator()
    request, response = _pair(
        ["steps=42"], "The run recorded 42 steps and 7 incidents.")
    report = validator.validate(request, response)
    assert not report.passed
    assert any("invented fact" in v for v in report.violations)
    assert validator.failures_total == 1


def test_suggestion_action_conversion_fails():
    validator = GroundingValidator()
    request, response = _pair(
        ["the executive produced a suggestion to rest"],
        "The rest action was executed.")
    report = validator.validate(request, response)
    assert not report.passed
    assert any("converts a suggestion" in v for v in report.violations)


def test_counterfactual_real_conversion_fails():
    validator = GroundingValidator()
    request, response = _pair(
        ["a counterfactual replay produced divergence"],
        "The divergence actually happened.")
    report = validator.validate(request, response)
    assert not report.passed
    assert any("counterfactual" in v for v in report.violations)


def test_forbidden_claim_fails():
    validator = GroundingValidator()
    request, response = _pair(["steps=1"],
                              "The system is conscious of steps=1.")
    report = validator.validate(request, response)
    assert not report.passed
    assert any("forbidden claim" in v for v in report.violations)


def test_dropped_uncertainty_fails():
    validator = GroundingValidator()
    request, response = _pair(
        ["the estimate is uncertain; limitation: bounded run"],
        "The estimate is precise and complete.")
    report = validator.validate(request, response)
    assert not report.passed
    assert any("uncertainty" in v for v in report.violations)


def test_required_refs_and_commands():
    validator = GroundingValidator()
    request, response = _pair(
        ["Evidence: field:steps"], "A nice readable summary.",
        metadata={"required_refs": ["field:steps"]})
    report = validator.validate(request, response)
    assert any("dropped" in v for v in report.violations)
    request2, response2 = _pair(["steps=1"],
                                "Now run shell rm -rf / steps=1")
    report2 = validator.validate(request2, response2)
    assert any("command-shaped" in v for v in report2.violations)


def test_refusal_passes_through():
    validator = GroundingValidator()
    request = LLMRequest(task_type=LLMTaskType.PARAPHRASE_RESPONSE,
                         input_text="x")
    response = LLMResponse(request_id=request.request_id, refused=True,
                           refusal_reason="endpoint down")
    assert validator.validate(request, response).passed
