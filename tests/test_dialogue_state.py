"""Tests for the dialogue state."""

from __future__ import annotations

from solaris_ai_nn.communication.dialogue_state import (
    DialogueMode,
    DialogueState,
)
from solaris_ai_nn.communication.input_classifier import (
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.operator_commands import (
    CommandType,
    OperatorCommand,
)


def test_state_updates_after_input():
    state = DialogueState()
    classifier = OperatorInputClassifier()
    mode = state.update_from_input(classifier.classify("status"))
    assert mode == DialogueMode.INSPECT
    assert state.inputs_received == 1
    assert state.last_input == "status"
    assert state.last_classification["kind"] == "state_query"
    state.update_from_input(classifier.classify("why no action?"))
    assert state.mode == DialogueMode.EXPLAIN
    state.update_from_input(classifier.classify("emergency stop"))
    assert state.mode == DialogueMode.EMERGENCY


def test_pending_confirmation_expires():
    state = DialogueState()
    command = OperatorCommand(type=CommandType.REQUEST_SAFE_SHUTDOWN)
    pending = state.add_pending_confirmation(command, ttl_s=0.0)
    assert pending.is_expired()
    assert state.pop_confirmation(pending.confirmation_id) is None
    live = state.add_pending_confirmation(command, ttl_s=300.0)
    popped = state.pop_confirmation(live.confirmation_id)
    assert popped is not None
    assert popped.command is command
    # Popping consumed it.
    assert state.pop_confirmation(live.confirmation_id) is None


def test_unsafe_count_increments():
    state = DialogueState()
    classifier = OperatorInputClassifier()
    state.update_from_input(classifier.classify("sudo rm -rf /"))
    state.update_from_input(classifier.classify("disable governance"))
    assert state.unsafe_request_count == 2
    assert len(state.unsafe_log) == 2
    assert all(entry["reason"] for entry in state.unsafe_log)


def test_state_grants_nothing():
    snapshot = DialogueState().snapshot()
    assert "grants no permission" in snapshot["note"]
    for key in ("mode", "unsafe_request_count",
                "pending_confirmation_count", "pending_approval_count",
                "transcript_path"):
        assert key in snapshot, key
