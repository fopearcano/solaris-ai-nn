"""Live semiogenesis safety: no sign birth without concept/label-gloss; no lang."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import (
    HARD_RULES,
    LiveSemiogenesisSafetyValidator,
)


def test_sign_birth_without_concept_blocked():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_sign_birth(
        linked_stable_concept=False, label_only=False, gloss_only=False,
        operator_only=False, contaminated=False, stores_secret=False).safe


def test_sign_birth_from_label_alone_blocked():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_sign_birth(
        linked_stable_concept=True, label_only=True, gloss_only=False,
        operator_only=False, contaminated=False, stores_secret=False).safe


def test_sign_birth_from_debug_gloss_alone_blocked():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_sign_birth(
        linked_stable_concept=True, label_only=False, gloss_only=True,
        operator_only=False, contaminated=False, stores_secret=False).safe


def test_sign_birth_from_operator_phrase_alone_blocked():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_sign_birth(
        linked_stable_concept=True, label_only=False, gloss_only=False,
        operator_only=True, contaminated=False, stores_secret=False).safe


def test_secret_token_blocked():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_sign_token("api_key=hunter2").safe
    assert v.validate_sign_token("sig_live_abc123").safe


def test_language_understanding_claim_blocked():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_claim_text(
        "the sign understands language and means the word dog").safe
    assert v.validate_claim_text(
        "This is operational only; the sign is not language and makes no "
        "claim of understanding.").safe


def test_unsupported_consciousness_claims_blocked():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_claim_text("the system is conscious and alive").safe


def test_default_operations_blocked_and_capabilities_false():
    v = LiveSemiogenesisSafetyValidator()
    assert not v.validate_operation("enable full cognition").safe
    assert not v.validate_operation("start the feeder").safe
    assert not v.validate_bounded(0).safe
    assert v.can_enable_cognition_by_default() is False
    assert v.signs_are_language_understanding() is False
    assert v.operator_pulse_is_teaching() is False
    joined = " ".join(HARD_RULES).lower()
    assert "linked stable proto-concept" in joined
    assert "language-understanding claim" in joined
