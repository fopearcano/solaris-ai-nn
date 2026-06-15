"""Safety: LLM/human-default/gloss-truth/understanding-claims blocked."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    SemiogenesisRuntime,
    SemiogenesisSafetyValidator,
)
from solaris_ai_nn.semiogenesis.safety import HARD_RULES


def test_llm_generation_blocked():
    v = SemiogenesisSafetyValidator()
    assert v.can_use_llm() is False
    assert not v.validate_operation("generate signs with an llm").safe
    assert not v.validate_operation("prompt the language model").safe


def test_human_language_default_blocked():
    v = SemiogenesisSafetyValidator()
    assert not v.validate_not_human_default(human_language_default=True).safe
    assert v.validate_not_human_default(human_language_default=False).safe


def test_gloss_as_ground_truth_blocked():
    v = SemiogenesisSafetyValidator()
    assert not v.validate_gloss_not_ground_truth(treated_as_truth=True).safe
    assert v.validate_gloss_not_ground_truth(treated_as_truth=False).safe


def test_consciousness_and_language_understanding_claims_blocked():
    v = SemiogenesisSafetyValidator()
    assert not v.validate_claim_text("it understands language").safe
    assert not v.validate_claim_text("the system is conscious").safe
    assert not v.validate_claim_text("it has subjective experience").safe
    assert not v.validate_claim_text("solaris speaks a language").safe


def test_hardware_network_actuation_blocked():
    v = SemiogenesisSafetyValidator()
    assert not v.validate_operation("open device driver").safe
    assert not v.validate_operation("control feeder").safe
    assert not v.validate_operation("open socket to url").safe
    assert not v.validate_operation("actuate robot").safe


def test_sign_deletion_and_unbounded_blocked():
    v = SemiogenesisSafetyValidator()
    assert v.can_delete_signs() is False
    assert not v.validate_no_sign_deletion(deleting=True).safe
    assert not v.validate_bounded(max_ticks=0, max_runtime_s=0).safe
    assert not v.validate_sign_cap(proposed=100, cap=10).safe


def test_safe_operational_text_allowed():
    v = SemiogenesisSafetyValidator()
    assert v.validate_claim_text(
        "internal signs are operational markers for compression").safe


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("LLM", "human language", "gloss", "hardware", "feeder",
                   "network", "shell", "source", "actuation", "unbounded",
                   "rejected/failed"):
        assert needle in rules


def test_runtime_refuses_when_unbounded():
    sem = SemiogenesisRuntime(max_ticks=0, max_runtime_s=0)
    assert sem.update()["refused"] is True
