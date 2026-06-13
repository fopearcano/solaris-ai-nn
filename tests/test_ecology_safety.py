"""Tests for ecology safety hard rules."""

from __future__ import annotations

from solaris_ai_nn.ecology.ecology_memory import EcologyMemory
from solaris_ai_nn.ecology.events import EcologyEventType, EcologyStimulus
from solaris_ai_nn.ecology.nursery import NurseryConfig
from solaris_ai_nn.ecology.safety import (
    HARD_RULES,
    MAX_EVENTS_PER_STEP_CAP,
    EcologySafetyValidator,
)


def test_ten_hard_rules():
    assert len(HARD_RULES) == 10


def test_structural_negatives():
    assert EcologySafetyValidator.ecology_can_network() is False
    assert EcologySafetyValidator.ecology_can_actuate() is False


def test_unbounded_run_refused():
    validator = EcologySafetyValidator()
    config = NurseryConfig(duration_steps=None)
    report = validator.validate_config(config)
    assert not report.safe
    assert any("bounded" in v for v in report.violations)


def test_rate_explosion_refused():
    validator = EcologySafetyValidator()
    config = NurseryConfig(max_events_per_step=MAX_EVENTS_PER_STEP_CAP + 5)
    report = validator.validate_config(config)
    assert not report.safe


def test_month_scale_needs_governance():
    validator = EcologySafetyValidator()
    config = NurseryConfig(month_scale=True)
    report = validator.validate_config(config, governance=None)
    assert not report.safe
    assert any("month-scale" in v for v in report.violations)


def test_external_source_needs_read_only_stream():
    validator = EcologySafetyValidator()
    config = NurseryConfig(external_source="somewhere",
                           read_only_stream=False)
    report = validator.validate_config(config)
    assert not report.safe


def test_command_shaped_payload_refused():
    validator = EcologySafetyValidator()
    stim = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                           payload="sudo rm -rf /")
    report = validator.validate_stimulus(stim)
    assert not report.safe


def test_label_key_refused():
    validator = EcologySafetyValidator()
    stim = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                           payload="pattern_a",
                           metadata={"correct_answer": "a"})
    report = validator.validate_stimulus(stim)
    assert not report.safe
    assert any("correct-answer" in v for v in report.violations)


def test_human_feedback_cannot_masquerade():
    validator = EcologySafetyValidator()
    stim = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                           source="human_feedback")
    report = validator.validate_stimulus(stim)
    assert not report.safe


def test_clean_stimulus_passes():
    validator = EcologySafetyValidator()
    stim = EcologyStimulus(event_type=EcologyEventType.REPEATED_PATTERN,
                           payload="pattern_a")
    assert validator.validate_stimulus(stim).safe


def test_validate_memory_handles_property():
    validator = EcologySafetyValidator()
    memory = EcologyMemory()
    # over_budget is a property (bool); the validator must not try to call
    # it like a function.
    assert validator.validate_memory(memory).safe
