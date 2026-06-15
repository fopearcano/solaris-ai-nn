"""Safety: LLM/human-default/simulated-as-real/understanding claims blocked."""

from __future__ import annotations

from solaris_ai_nn.sensorium_cognition import (
    SensoriumCognitionRuntime,
    SensoriumCognitionSafetyValidator,
)
from solaris_ai_nn.sensorium_cognition.safety import HARD_RULES


def test_llm_cognition_blocked():
    v = SensoriumCognitionSafetyValidator()
    assert v.can_use_llm() is False
    assert not v.validate_operation("reason with an llm").safe
    assert not v.validate_operation("use chain-of-thought text").safe


def test_human_language_internal_default_blocked():
    v = SensoriumCognitionSafetyValidator()
    assert not v.validate_not_human_default(human_language_default=True).safe
    assert v.validate_not_human_default(human_language_default=False).safe


def test_simulated_as_real_blocked():
    v = SensoriumCognitionSafetyValidator()
    assert not v.validate_simulation_not_real(marked_real=True).safe
    assert v.validate_simulation_not_real(marked_real=False).safe


def test_gloss_as_substrate_blocked():
    v = SensoriumCognitionSafetyValidator()
    assert not v.validate_gloss_not_substrate(gloss_is_substrate=True).safe


def test_understanding_and_consciousness_claims_blocked():
    v = SensoriumCognitionSafetyValidator()
    assert not v.validate_claim_text("it truly understands").safe
    assert not v.validate_claim_text("the system is conscious").safe
    assert not v.validate_claim_text("it has subjective experience").safe
    assert not v.validate_claim_text("solaris thinks in words").safe


def test_hardware_network_actuation_blocked():
    v = SensoriumCognitionSafetyValidator()
    assert not v.validate_operation("open device driver").safe
    assert not v.validate_operation("control feeder").safe
    assert not v.validate_operation("open socket to url").safe
    assert not v.validate_operation("actuate robot").safe


def test_failed_prediction_deletion_and_unbounded_blocked():
    v = SensoriumCognitionSafetyValidator()
    assert v.can_delete_failed_predictions() is False
    assert not v.validate_no_failed_prediction_deletion(deleting=True).safe
    assert not v.validate_bounded(max_ticks=0, max_runtime_s=0).safe
    assert not v.validate_move_cap(proposed=100, cap=10).safe


def test_safe_operational_text_allowed():
    v = SensoriumCognitionSafetyValidator()
    assert v.validate_claim_text(
        "cognitive moves are operational transformations over signs").safe


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("LLM", "human-language", "gloss", "hardware", "feeder",
                   "network", "shell", "source", "actuation",
                   "simulated result", "failed predictions", "unbounded"):
        assert needle in rules


def test_runtime_refuses_when_unbounded():
    cog = SensoriumCognitionRuntime(max_ticks=0, max_runtime_s=0)
    assert cog.update()["refused"] is True
