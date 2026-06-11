"""Tests for the long-run drift monitor."""

from __future__ import annotations

from solaris_ai_nn.developmental.drift_monitor import LongRunDriftMonitor


def test_slow_drift_recorded():
    monitor = LongRunDriftMonitor()
    monitor.observe({"substrate_state_norm": 4.0,
                     "habit_weight_total": 10.0})
    report = monitor.observe({"substrate_state_norm": 4.1,
                              "habit_weight_total": 10.5})
    assert report.classification == "healthy_slow"
    assert not report.warnings
    assert report.drift_velocity > 0
    metric = {m.name: m for m in report.metrics}["substrate_state_norm"]
    assert metric.previous == 4.0
    assert metric.current == 4.1


def test_runaway_drift_warns():
    monitor = LongRunDriftMonitor()
    monitor.observe({"substrate_state_norm": 2.0})
    report = monitor.observe({"substrate_state_norm": 20.0})
    assert report.classification == "fast_warning"
    assert any("uncontrolled drift" in w for w in report.warnings)
    assert monitor.fast_warnings_total == 1


def test_zero_drift_inertia_warns():
    monitor = LongRunDriftMonitor()
    report = None
    for _ in range(7):
        report = monitor.observe({"substrate_state_norm": 3.0,
                                  "mysterium_pressure": 0.5})
    assert report.classification == "inert_warning"
    assert any("inert" in w or "dead" in w for w in report.warnings)
    snapshot = monitor.snapshot()
    assert snapshot["flat_windows"] >= 5
    assert "total flatness" in snapshot["note"]


def test_first_observation_is_baseline():
    monitor = LongRunDriftMonitor()
    report = monitor.observe({"substrate_state_norm": 99.0})
    # No previous window: nothing to warn about yet.
    assert report.classification == "healthy_slow"
    assert not report.warnings
