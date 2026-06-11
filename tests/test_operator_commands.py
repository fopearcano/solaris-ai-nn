"""Tests for the typed operator command set."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.operator_commands import (
    FORBIDDEN_COMMAND_TYPES,
    CommandType,
    OperatorCommand,
    command_from_classification,
    is_forbidden_type,
)


def test_allowed_command_serializes():
    command = OperatorCommand(type=CommandType.SHOW_STATUS,
                              raw_text="status", operator="op-1")
    data = command.to_dict()
    for key in ("command_id", "type", "raw_text", "parsed_args",
                "operator", "created_at", "requires_confirmation",
                "requires_governance", "safety_status",
                "governance_status", "metadata"):
        assert key in data, key
    assert data["forbidden"] is False
    assert data["safety_status"] == "unchecked"


def test_forbidden_command_detected():
    assert len(FORBIDDEN_COMMAND_TYPES) == 9
    for command_type in ("execute_shell", "open_network",
                         "modify_source_code", "disable_governance",
                         "disable_emergency_stop",
                         "commit_sidecar_action",
                         "real_world_actuation",
                         "delete_unapproved_files",
                         "unbounded_run_without_approval"):
        assert is_forbidden_type(command_type), command_type
        assert OperatorCommand(type=command_type).forbidden
    # No overlap between allowed and forbidden sets.
    assert not set(CommandType.ALL) & set(FORBIDDEN_COMMAND_TYPES)


def test_command_requiring_confirmation_marked():
    shutdown = OperatorCommand(type=CommandType.REQUEST_SAFE_SHUTDOWN)
    assert shutdown.requires_confirmation
    benchmark = OperatorCommand(type=CommandType.RUN_BOUNDED_BENCHMARK)
    assert benchmark.requires_confirmation
    assert benchmark.requires_governance
    status = OperatorCommand(type=CommandType.SHOW_STATUS)
    assert not status.requires_confirmation


def test_command_from_classification_mapping():
    classifier = OperatorInputClassifier()
    cases = (
        ("status", CommandType.SHOW_STATUS),
        ("generate self-report", CommandType.GENERATE_REPORT),
        ("approve request ab12", CommandType.APPROVE_GOVERNANCE_REQUEST),
        ("add operator note: x", CommandType.ADD_OPERATOR_NOTE),
        ("emergency stop", CommandType.REQUEST_SAFE_SHUTDOWN),
        ("run a checkpoint", CommandType.REQUEST_CHECKPOINT),
    )
    for text, expected in cases:
        command = command_from_classification(classifier.classify(text),
                                              operator="op-1")
        assert command is not None, text
        assert command.type == expected, text
        assert command.operator == "op-1"
    # Unknown classifications produce no command at all.
    assert command_from_classification(
        classifier.classify("blorp fizzle")) is None
