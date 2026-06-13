"""Tests for ecology cycles and rhythm modulation."""

from __future__ import annotations

from solaris_ai_nn.ecology.cycles import (
    Cycle,
    CycleManager,
    CycleType,
)


def test_eight_cycle_types():
    assert len(CycleType.ALL) == 8


def test_phase_at_is_periodic():
    cycle = Cycle(cycle_type=CycleType.DAY_NIGHT, period=24,
                  phases=("day", "night"))
    assert cycle.phase_at(0) == "day"
    assert cycle.phase_at(12) == "night"
    assert cycle.phase_at(24) == cycle.phase_at(0)


def test_manager_records_phase_changes():
    manager = CycleManager(active_cycles=[CycleType.DAY_NIGHT])
    changes_seen = 0
    last = None
    for step in range(48):
        state = manager.update(step)
        phase = state.phases[CycleType.DAY_NIGHT]
        if last is not None and phase != last:
            changes_seen += 1
        last = phase
    assert manager.phase_changes == changes_seen
    assert manager.phase_changes >= 2


def test_modulation_in_silence_lowers_frequency():
    manager = CycleManager(active_cycles=[CycleType.SIGNAL_SILENCE])
    signal_state = manager.state_at(0)
    silence_state = manager.state_at(15)
    freq_signal, _ = manager.modulation(signal_state)
    freq_silence, _ = manager.modulation(silence_state)
    assert freq_silence < freq_signal


def test_in_silence_phase_detection():
    manager = CycleManager(active_cycles=[CycleType.SIGNAL_SILENCE])
    assert manager.in_silence_phase(manager.state_at(15)) is True
    assert manager.in_silence_phase(manager.state_at(0)) is False


def test_deterministic_state_at():
    a = CycleManager(active_cycles=list(CycleType.ALL))
    b = CycleManager(active_cycles=list(CycleType.ALL))
    for step in range(60):
        assert a.state_at(step).phases == b.state_at(step).phases


def test_snapshot_shape():
    manager = CycleManager(active_cycles=[CycleType.DAY_NIGHT])
    manager.update(0)
    snap = manager.snapshot()
    assert "active_cycles" in snap
    assert "phase_changes" in snap
