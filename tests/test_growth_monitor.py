"""Tests for the growth monitor."""

from __future__ import annotations

import json

from solaris_ai_nn.developmental.growth_monitor import GrowthMonitor


def test_accumulation_vs_structural_change_distinguished():
    monitor = GrowthMonitor()
    monitor.observe({"world_model_node_count": 10,
                     "stable_habit_count": 2,
                     "consolidated_schema_count": 0})
    accumulating = monitor.observe({"world_model_node_count": 40,
                                    "stable_habit_count": 2,
                                    "consolidated_schema_count": 0})
    assert accumulating.classification == "accumulation"
    assert accumulating.structural_change_score < 0.2
    consolidating = monitor.observe({"world_model_node_count": 42,
                                     "stable_habit_count": 4,
                                     "consolidated_schema_count": 3})
    assert consolidating.classification == "consolidation"
    assert consolidating.structural_change_score > 0.0


def test_stagnation_detected():
    monitor = GrowthMonitor()
    flat = {"world_model_node_count": 20, "stable_habit_count": 3,
            "consolidated_schema_count": 1}
    monitor.observe(dict(flat))
    for _ in range(3):
        snapshot = monitor.observe(dict(flat))
    assert snapshot.classification == "stagnation"
    assert monitor.stagnation_windows == 3
    # Movement resets the stagnation counter.
    monitor.observe({**flat, "world_model_node_count": 25})
    assert monitor.stagnation_windows == 0


def test_regression_and_phase_transition_labels():
    monitor = GrowthMonitor()
    monitor.observe({"prediction_accuracy_trend": 0.5,
                     "stable_habit_count": 5})
    regression = monitor.observe({"prediction_accuracy_trend": 0.2,
                                  "stable_habit_count": 5})
    assert regression.classification == "regression"
    monitor2 = GrowthMonitor()
    monitor2.observe({"prediction_accuracy_trend": 0.1,
                      "mysterium_trend": 0.2})
    jump = monitor2.observe({"prediction_accuracy_trend": 0.6,
                             "mysterium_trend": 0.2})
    assert jump.classification == "phase_transition"
    assert any("not proof" in r for r in jump.reasons)


def test_growth_snapshot_serializes():
    monitor = GrowthMonitor()
    snapshot = monitor.observe({"stable_habit_count": 1,
                                "world_model_node_count": 5})
    json.dumps(snapshot.to_dict(), default=str)
    assert "metrics" in snapshot.to_dict()
    assert "deltas" in snapshot.to_dict()
    overview = monitor.snapshot()
    assert overview["observations"] == 1
    assert "not claims of development" in overview["note"]
