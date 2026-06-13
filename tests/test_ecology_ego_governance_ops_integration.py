"""Integration: ecology events attribute, govern, and surface in ops."""

from __future__ import annotations

from solaris_ai_nn.ecology.events import EcologyEventType, EcologyStimulus
from solaris_ai_nn.ecology.nursery import NurseryConfig
from solaris_ai_nn.ecology.safety import EcologySafetyValidator
from solaris_ai_nn.ego.ownership import (
    EXTERNAL_CATEGORIES,
    OwnershipAttributor,
)


def test_nursery_event_attributed_as_nursery_not_operator():
    attributor = OwnershipAttributor()
    result = attributor.attribute_event(
        {"source": "developmental_nursery", "kind": "regular_signal",
         "payload": "pattern_a"})
    assert result.category == "generated_by_developmental_nursery"
    assert result.category in EXTERNAL_CATEGORIES
    assert not result.is_executable_instruction
    assert any("never an operator command" in r for r in result.reasons)


def test_simulated_environment_attribution():
    attributor = OwnershipAttributor()
    result = attributor.attribute_event(
        {"source": "simulated_environment", "kind": "boundary_event"})
    assert result.category == "simulated_environment_input"
    assert any("simulated world" in r for r in result.reasons)


def test_ecology_never_human_feedback():
    # Even a payload shaped like an instruction is dropped by safety before
    # it can be emitted, so the ego never sees it as a command.
    validator = EcologySafetyValidator()
    stim = EcologyStimulus(event_type=EcologyEventType.REGULAR_SIGNAL,
                           payload="approve request 1234")
    assert not validator.validate_stimulus(stim).safe


def test_month_scale_blocked_without_governance():
    validator = EcologySafetyValidator()
    report = validator.validate_config(NurseryConfig(month_scale=True))
    assert not report.safe


def test_supervisor_ecology_incident_types_registered():
    from solaris_ai_nn.ops import incident as I

    for name in (I.ECOLOGY_STIMULUS_RATE_HIGH, I.ECOLOGY_SILENCE_TOO_LONG,
                 I.ECOLOGY_ANOMALY_RATE_HIGH, I.ECOLOGY_MEMORY_GROWTH,
                 I.ECOLOGY_REPLAY_MISMATCH):
        assert name in I.INCIDENT_TYPES
