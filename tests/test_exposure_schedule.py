"""Pilot-2 exposure schedule: alternation, quiet windows, simulated labels."""

from __future__ import annotations

from solaris_ai_nn.pilot2 import ExposureCondition, ExposureSchedule, ExposureWindow


def test_alternating_windows_generated():
    sched = ExposureSchedule.alternating(cycles=2, window_steps=10)
    assert len(sched.windows) == 10
    conditions = {w.condition for w in sched.windows}
    assert ExposureCondition.NURSERY_ONLY in conditions
    assert ExposureCondition.SENSORY_ONLY in conditions
    assert ExposureCondition.MIXED in conditions


def test_quiet_windows_preserved():
    sched = ExposureSchedule.alternating(cycles=2)
    assert sched.quiet_window_count > 0
    assert not sched.validate()  # no warnings about starved latent replay


def test_simulated_labels_preserved():
    sched = ExposureSchedule.alternating(cycles=1, simulated=True)
    assert all(w.simulated_acceleration for w in sched.windows)


def test_comparison_windows_explicit():
    sched = ExposureSchedule.alternating(cycles=1)
    groups = sched.comparison_windows()
    assert ExposureCondition.NURSERY_ONLY in groups
    assert ExposureCondition.SENSORY_ONLY in groups


def test_unknown_condition_normalized():
    w = ExposureWindow(index=0, condition="not_a_condition")
    assert w.condition == ExposureCondition.MIXED


def test_long_unlabelled_window_warns():
    sched = ExposureSchedule()
    sched.windows.append(ExposureWindow(index=0,
                                        condition=ExposureCondition.SENSORY_ONLY,
                                        steps=9000))
    assert any("simulated label" in w for w in sched.validate())
