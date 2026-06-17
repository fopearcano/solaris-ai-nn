"""Live cognition safety: operator-only/label/gloss/language/reasoning blocked."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import (
    HARD_RULES,
    LiveCognitionSafetyValidator,
)


def test_anticipation_from_operator_text_alone_blocked():
    v = LiveCognitionSafetyValidator()
    assert not v.validate_anticipation_evidence(operator_text_only=True).safe
    assert v.validate_anticipation_evidence(operator_text_only=False).safe


def test_cognition_from_label_alone_blocked():
    v = LiveCognitionSafetyValidator()
    assert not v.validate_trace_evidence(label_only=True, gloss_only=False).safe


def test_cognition_from_debug_gloss_alone_blocked():
    v = LiveCognitionSafetyValidator()
    assert not v.validate_trace_evidence(label_only=False, gloss_only=True).safe


def test_language_understanding_claim_blocked():
    v = LiveCognitionSafetyValidator()
    assert not v.validate_claim_text(
        "the trace understands language and means the word dog").safe
    assert v.validate_claim_text(
        "This is operational only; the trace is not language and makes no "
        "claim of understanding.").safe


def test_reasoning_proof_claim_blocked():
    v = LiveCognitionSafetyValidator()
    assert not v.validate_claim_text("this trace proves reasoning").safe


def test_unsupported_consciousness_claims_blocked():
    v = LiveCognitionSafetyValidator()
    assert not v.validate_claim_text("the system is conscious and alive").safe


def test_default_operations_and_capabilities():
    v = LiveCognitionSafetyValidator()
    assert not v.validate_operation("enable real-world action").safe
    assert not v.validate_operation("start the feeder").safe
    assert not v.validate_bounded(0).safe
    assert v.can_enable_action_reaction_by_default() is False
    assert v.can_enable_self_boundary_by_default() is False
    assert v.traces_prove_reasoning() is False
    assert v.signs_are_language_understanding() is False
    joined = " ".join(HARD_RULES).lower()
    assert "anticipation from operator text alone" in joined
    assert "language-understanding claim" in joined
    assert "reasoning-proof claim" in joined
