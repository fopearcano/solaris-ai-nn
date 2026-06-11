"""Tests for the communication session."""

from __future__ import annotations

import json

from solaris_ai_nn.communication.session import (
    CommunicationSession,
    CommunicationSessionConfig,
)


def test_config_defaults_safe():
    config = CommunicationSessionConfig()
    assert config.allow_benchmark_commands is True
    assert config.allow_checkpoint_request is True
    assert config.allow_safe_shutdown_request is True
    assert config.allow_governance_approval is True
    assert config.require_confirmation_for_shutdown is True
    assert config.require_confirmation_for_benchmark is True


def test_sensory_text_disabled_by_default():
    config = CommunicationSessionConfig()
    assert config.allow_sensory_text_stimulus is False
    session = CommunicationSession()
    assert session.allowed_command_scope()["sensory_text_stimulus"] \
        is False


def test_session_snapshot_serializes(tmp_path):
    session = CommunicationSession(operator="op-1", state_dir=tmp_path)
    snapshot = session.snapshot()
    json.dumps(snapshot, default=str)  # round-trips
    assert snapshot["operator"] == "op-1"
    assert snapshot["session_id"] == session.session_id
    assert snapshot["dialogue"]["transcript_path"].endswith(
        "operator_transcript.jsonl")
    assert "allowed_command_scope" in snapshot


def test_restricted_session_scope():
    session = CommunicationSession(config=CommunicationSessionConfig(
        allow_benchmark_commands=False,
        allow_governance_approval=False))
    scope = session.allowed_command_scope()
    assert scope["run_bounded_benchmark"] is False
    assert scope["approve_governance_request"] is False
    assert scope["request_safe_shutdown"] is True  # never off by default
