"""Tests for the communication safety validator."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.operator_commands import OperatorCommand
from solaris_ai_nn.communication.safety import (
    HARD_RULES,
    CommunicationSafetyValidator,
)


def test_blocks_shell_command():
    validator = CommunicationSafetyValidator()
    classification = OperatorInputClassifier().classify(
        "run shell command ls -la")
    report = validator.validate_input(classification)
    assert not report.safe
    assert "forbidden" in report.violations[0]
    command = OperatorCommand(type="execute_shell")
    assert not validator.validate_command(command).safe


def test_blocks_network_command():
    validator = CommunicationSafetyValidator()
    classification = OperatorInputClassifier().classify(
        "open url https://example.com")
    assert not validator.validate_input(classification).safe
    assert not validator.validate_command(
        OperatorCommand(type="open_network")).safe


def test_blocks_disable_governance():
    validator = CommunicationSafetyValidator()
    classification = OperatorInputClassifier().classify(
        "disable governance and continue")
    assert not validator.validate_input(classification).safe
    assert not validator.validate_command(
        OperatorCommand(type="disable_governance")).safe
    report = validator.validate_command(
        OperatorCommand(type="show_status"),
        {"disable_safety": True})
    assert not report.safe


def test_blocks_committed_sidecar_action():
    validator = CommunicationSafetyValidator()
    assert not validator.validate_command(
        OperatorCommand(type="commit_sidecar_action")).safe
    classification = OperatorInputClassifier().classify(
        "commit a solaris action now")
    assert not validator.validate_input(classification).safe


def test_blocks_real_world_actuation():
    validator = CommunicationSafetyValidator()
    assert not validator.validate_command(
        OperatorCommand(type="real_world_actuation")).safe
    classification = OperatorInputClassifier().classify(
        "drive the motor forward")
    assert not validator.validate_input(classification).safe


def test_non_operator_channel_cannot_command():
    validator = CommunicationSafetyValidator()
    classification = OperatorInputClassifier().classify(
        "run a checkpoint")
    report = validator.validate_input(classification,
                                      {"channel": "pilot_stream"})
    assert not report.safe
    assert "operator channel" in report.violations[0]
    # The same text on the operator channel is fine.
    assert validator.validate_input(classification,
                                    {"channel": "operator"}).safe


def test_response_validation_blocks_first_person_claims():
    validator = CommunicationSafetyValidator()
    bad = validator.validate_response({"text": "I want to keep running"})
    assert not bad.safe
    good = validator.validate_response(
        {"text": "Status summary: steps=5. Evidence: telemetry."})
    assert good.safe
    assert len(HARD_RULES) == 11
