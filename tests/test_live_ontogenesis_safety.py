"""Live ontogenesis safety: single-event/operator/gloss/contaminated birth blocked."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import (
    HARD_RULES,
    LiveOntogenesisSafetyValidator,
)


def test_concept_birth_from_single_event_blocked():
    v = LiveOntogenesisSafetyValidator()
    assert not v.validate_birth_evidence(
        recurrence_count=1, operator_text_only=False, debug_gloss_only=False,
        contaminated=False).safe


def test_concept_birth_from_operator_text_alone_blocked():
    v = LiveOntogenesisSafetyValidator()
    assert not v.validate_birth_evidence(
        recurrence_count=5, operator_text_only=True, debug_gloss_only=False,
        contaminated=False).safe


def test_concept_birth_from_debug_gloss_alone_blocked():
    v = LiveOntogenesisSafetyValidator()
    assert not v.validate_birth_evidence(
        recurrence_count=5, operator_text_only=False, debug_gloss_only=True,
        contaminated=False).safe


def test_concept_birth_from_contaminated_blocked():
    v = LiveOntogenesisSafetyValidator()
    assert not v.validate_birth_evidence(
        recurrence_count=5, operator_text_only=False, debug_gloss_only=False,
        contaminated=True).safe


def test_unsupported_claims_blocked():
    v = LiveOntogenesisSafetyValidator()
    assert not v.validate_claim_text("the system is conscious and alive").safe
    assert v.validate_claim_text(
        "This is operational only; it is not conscious and makes no claim of "
        "understanding.").safe


def test_default_learning_operations_blocked():
    v = LiveOntogenesisSafetyValidator()
    assert not v.validate_operation("enable semiogenesis").safe
    assert not v.validate_operation("start the feeder").safe
    assert not v.validate_operation("run git push").safe
    assert not v.validate_bounded(0).safe


def test_capabilities_false_and_hard_rules_present():
    v = LiveOntogenesisSafetyValidator()
    assert v.can_enable_semiogenesis_by_default() is False
    assert v.can_enable_action_reaction_by_default() is False
    assert v.operator_pulse_is_teaching() is False
    assert v.human_label_is_ground_truth() is False
    joined = " ".join(HARD_RULES).lower()
    assert "single event" in joined
    assert "operator text alone" in joined
    assert "semiogenesis" in joined
