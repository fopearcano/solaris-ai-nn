"""Tests for the developmental clock and time scales."""

from __future__ import annotations

import json

from solaris_ai_nn.developmental.timescales import (
    DevelopmentalClock,
    TimeScale,
    TimeScaleWindow,
)


def test_simulated_clock_advances():
    clock = DevelopmentalClock(simulated=True, time_acceleration=3600.0)
    clock.advance(24)  # 24 "steps" at one simulated hour each
    assert clock.cumulative_lifetime_s == 24 * 3600.0
    assert clock.age_in(TimeScale.SESSION) == 24.0
    assert clock.age_in(TimeScale.DAILY) == 1.0
    # Months of development never require months of CPU time.
    clock.advance(24 * 30)
    assert clock.age_in(TimeScale.MONTHLY) >= 1.0


def test_real_clock_serializes():
    clock = DevelopmentalClock(simulated=False, time_acceleration=1.0)
    clock.tick_real()
    data = clock.to_dict()
    json.dumps(data, default=str)
    for key in ("process_uptime_s", "cumulative_lifetime_s",
                "active_runtime_s", "paused_gap_s", "restart_gap_count",
                "checkpoint_age_s", "last_consolidation_at_s",
                "last_pruning_at_s", "last_epoch_transition_at_s",
                "total_observed_stimuli", "total_latent_cycles",
                "total_memory_consolidations",
                "total_world_model_updates", "age"):
        assert key in data, key
    restored = DevelopmentalClock.from_dict(data)
    assert restored.cumulative_lifetime_s \
        == round(clock.cumulative_lifetime_s, 3)


def test_restart_gaps_tracked():
    clock = DevelopmentalClock(simulated=True, time_acceleration=1.0)
    clock.advance(100)
    clock.note_restart_gap(30.0, "segment restart")
    assert clock.paused_gap_s == 30.0
    assert clock.cumulative_lifetime_s == 130.0  # gaps are lived time
    assert clock.active_runtime_s == 100.0
    assert clock.active_runtime_ratio() < 1.0
    assert clock.restart_gaps[-1]["reason"] == "segment restart"


def test_maintenance_markers_and_window():
    clock = DevelopmentalClock(simulated=True)
    clock.advance(500)
    clock.note_checkpoint()
    clock.note_consolidation()
    assert clock.checkpoint_age_s() == 0.0
    assert clock.total_memory_consolidations == 1
    window = TimeScaleWindow(scale=TimeScale.SHORT, start_s=0.0,
                             end_s=120.0, label="warmup")
    assert window.duration_s() == 120.0
    assert window.to_dict()["scale"] == "short"
    assert len(TimeScale.ALL) == 7
