"""Tests for the latent mode state machine."""

from __future__ import annotations

import pytest

from solaris_ai_nn.latent.modes import (
    VALID_TRANSITIONS,
    LatentMode,
    SleepWakeController,
)


def test_mode_transitions_valid():
    c = SleepWakeController()
    assert c.mode == LatentMode.AWAKE
    c.transition(LatentMode.QUIET, "low input", step=10)
    c.transition(LatentMode.SLEEP, "silence", step=20)
    c.transition(LatentMode.CONSOLIDATION, "trace big", step=21)
    c.transition(LatentMode.REPLAY, "replay due", step=22)
    c.transition(LatentMode.DREAM, "pressure high", step=23)
    c.transition(LatentMode.WAKE_TRANSITION, "done", step=24)
    c.transition(LatentMode.AWAKE, "summary exposed", step=25)
    assert c.mode == LatentMode.AWAKE
    assert len(c.history) == 7
    assert all(t.reason for t in c.history)  # every transition logged


def test_illegal_transitions_rejected():
    c = SleepWakeController()
    with pytest.raises(ValueError):
        c.transition(LatentMode.DREAM, "skip the ladder")  # awake -> dream
    with pytest.raises(ValueError):
        c.transition("hibernate", "unknown mode")
    c.transition(LatentMode.SLEEP, "ok")
    with pytest.raises(ValueError):
        c.transition(LatentMode.AWAKE, "must pass wake_transition")


def test_sleep_dream_modes_block_external_actions():
    c = SleepWakeController()
    assert c.can_execute_external_actions()  # awake
    c.transition(LatentMode.QUIET, "x")
    assert c.can_execute_external_actions()  # quiet still may act
    c.transition(LatentMode.SLEEP, "x")
    assert not c.can_execute_external_actions()
    for mode in (LatentMode.CONSOLIDATION, LatentMode.REPLAY):
        c.transition(mode, "x")
        assert not c.can_execute_external_actions(), mode
    c.transition(LatentMode.DREAM, "x")
    assert not c.can_execute_external_actions()
    assert c.is_latent()
    c.transition(LatentMode.WAKE_TRANSITION, "x")
    assert not c.can_execute_external_actions()  # still not until awake


def test_wake_transition_records_summary():
    c = SleepWakeController()
    c.transition(LatentMode.SLEEP, "silence", step=50)
    transitions = c.wake({"replays": 3, "schemas": 2}, "cycle complete",
                         step=55)
    assert [t.to_mode for t in transitions] == [LatentMode.WAKE_TRANSITION,
                                                LatentMode.AWAKE]
    assert c.last_wake_summary["replays"] == 3
    assert c.last_wake_summary["reason"] == "cycle complete"
    assert c.mode == LatentMode.AWAKE


def test_state_tracking_fields():
    c = SleepWakeController()
    c.note_stimulus(ts=100.0)
    assert c.state.last_stimulus_ts == 100.0
    assert c.state.silence_duration == 0
    for _ in range(4):
        c.note_silence()
    assert c.state.silence_duration == 4
    c.note_action(ts=101.0)
    c.note_consolidation()
    c.note_replay()
    assert c.state.last_consolidation_ts > 0
    assert c.state.last_replay_ts > 0
    c.update_proxies(input_rate=0.5, activity_norm=10.0,
                     steps_since_consolidation=250)
    assert 0.0 <= c.state.energy_proxy <= 1.0
    assert 0.0 <= c.state.fatigue_proxy <= 1.0
    snap = c.snapshot()
    assert snap["state"]["mode"] == LatentMode.AWAKE
    assert "mode_duration_s" in snap["state"]


def test_every_mode_has_an_exit():
    for mode in LatentMode.ALL:
        assert VALID_TRANSITIONS.get(mode), f"{mode} has no exit"
