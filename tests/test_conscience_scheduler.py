"""Conscience scheduler: cheap phases every step, heavy scans slower."""

from __future__ import annotations

import pytest

from solaris_ai_nn.conscience import (
    ConscienceScheduler,
    ScheduleCadence,
    ScheduleSlot,
)


def test_default_slots_present():
    s = ConscienceScheduler()
    assert "heartbeat" in s.slots
    assert "logos_scan" in s.slots


def test_heartbeat_runs_every_step_logos_slower():
    s = ConscienceScheduler()
    heartbeat_runs = logos_runs = 0
    for step in range(60):
        due = s.due_phases(step)
        heartbeat_runs += int(due["heartbeat"])
        logos_runs += int(due["logos_scan"])
    assert heartbeat_runs == 60
    assert logos_runs < heartbeat_runs


def test_emergency_only_cheap_phases_run():
    s = ConscienceScheduler()
    due = s.due_phases(5, emergency=True)
    assert due["heartbeat"] is True
    assert due["logos_scan"] is False


def test_unknown_cadence_rejected():
    with pytest.raises(ValueError):
        ScheduleSlot(phase="x", cadence="not_a_cadence")


def test_every_n_slot_due_logic():
    slot = ScheduleSlot(phase="x", cadence=ScheduleCadence.EVERY_N_STEPS,
                        every_n=10)
    assert slot.due(0) and slot.due(10) and not slot.due(7)


def test_skip_count_increments():
    s = ConscienceScheduler()
    for step in range(30):
        s.due_phases(step)
    assert s.skip_count > 0
    snap = s.snapshot()
    assert snap["skip_count"] == s.skip_count
