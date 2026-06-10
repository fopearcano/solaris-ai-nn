"""Tests for IntegrationState."""

from __future__ import annotations

from solaris_ai_nn.integration.integration_state import IntegrationState


def test_serializes_to_dict():
    state = IntegrationState(observe_only=True, compatibility_level="sidecar_ready")
    d = state.to_dict()
    for key in ("attached", "observe_only", "compatibility_level",
                "signals_observed", "signals_by_type", "suggestions_produced",
                "suggestions_published", "errors", "last_signal_ts",
                "last_suggestion_ts", "bus_type", "substrate_type",
                "telemetry_summary", "action_authority"):
        assert key in d
    assert d["action_authority"] is False  # invariant


def test_counters_update_correctly():
    state = IntegrationState()
    state.record_signal("Stimulus")
    state.record_signal("Stimulus")
    state.record_signal("Reaction")
    state.record_suggestion(published=True)
    state.record_suggestion(published=False)
    state.record_rejection()
    state.record_reaction()

    assert state.signals_observed == 3
    assert state.signals_by_type == {"Stimulus": 2, "Reaction": 1}
    assert state.suggestions_produced == 2
    assert state.suggestions_published == 1
    assert state.suggestions_rejected == 1
    assert state.reactions_learned == 1
    assert state.last_signal_ts > 0
    assert state.last_suggestion_ts > 0


def test_error_recording_is_capped():
    state = IntegrationState()
    for i in range(60):
        state.record_error(f"e{i}", cap=50)
    assert len(state.errors) == 50
    assert state.errors[-1] == "e59"
    assert state.to_dict()["error_count"] == 50


def test_action_authority_cannot_be_serialized_true():
    state = IntegrationState()
    state.action_authority = True  # even if someone flips the attr...
    assert state.to_dict()["action_authority"] is False  # ...the dict says no
