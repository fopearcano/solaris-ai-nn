"""Tests for the response builder."""

from __future__ import annotations

from solaris_ai_nn.communication.response_builder import ResponseBuilder
from solaris_ai_nn.governance.compliance import ClaimGuard


def test_status_response_grounded():
    builder = ResponseBuilder()
    response = builder.status_response("steps=10; health=ok",
                                       ["field:steps", "field:health"])
    assert response.grounded
    assert response.evidence_refs == ["field:steps", "field:health"]
    assert "Status summary" in response.text
    assert response.limitations  # the mandatory framing is attached


def test_unsafe_response_refuses_clearly():
    builder = ResponseBuilder()
    response = builder.unsafe_response(
        "shell/OS command execution is forbidden")
    assert response.kind == "unsafe_refusal"
    assert response.safety_status == "refused"
    assert "was refused because" in response.text
    assert not response.executed
    assert response.suggested_next_operator_action


def test_claim_guard_scans_response():
    builder = ResponseBuilder()
    response = builder.status_response("all metrics nominal",
                                       ["telemetry"])
    assert response.claim_guard_safe
    assert ClaimGuard().is_safe(response.text)
    # An explanation carrying unsafe wording gets rewritten, not emitted.
    risky = builder.explanation_response(
        "the system wanted to rest and felt tired", ["test"])
    assert risky.claim_guard_safe
    assert ClaimGuard().is_safe(risky.text)
    assert builder.claim_guard_warnings >= 1


def test_missing_data_response_says_unknown():
    builder = ResponseBuilder()
    response = builder.no_evidence_response()
    assert response.text == "The system has no evidence for that answer."
    missing = builder.missing_component_response("world_model")
    assert "not attached" in missing.text
    unknown = builder.unknown_response()
    assert "Nothing was executed" in unknown.text


def test_request_recorded_never_claims_execution():
    builder = ResponseBuilder()
    response = builder.request_recorded_response(
        "request_checkpoint", "the runtime/ops layer", ["command:abc"])
    assert response.executed is False
    assert "was not executed" in response.text
    assert "recorded as a request" in response.text


def test_no_first_person_claims_possible():
    from solaris_ai_nn.communication.templates import TEMPLATES

    for template_id, template in TEMPLATES.items():
        lowered = template.lower()
        for forbidden in ("i want", "i feel", "i am conscious",
                          "i am alive"):
            assert forbidden not in lowered, template_id
