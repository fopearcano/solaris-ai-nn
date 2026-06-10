"""Tests for the complexity pressure monitor."""

from __future__ import annotations

from solaris_ai_nn.latent.complexity_pressure import (
    ComplexityDecision,
    ComplexityPressureMonitor,
)


def test_detects_inertia():
    monitor = ComplexityPressureMonitor()
    reading = monitor.evaluate({"state_norm": 0.0, "activity_rate": 0.0,
                                "state_drift": 0.0})
    assert reading.decision == ComplexityDecision.FLAG_INERTIA
    assert reading.scores["inertia"] >= 0.9


def test_detects_runaway_activity():
    monitor = ComplexityPressureMonitor(runaway_norm=50.0)
    reading = monitor.evaluate({"state_norm": 80.0, "activity_rate": 1.0,
                                "recent_actions": ["a", "b", "c"] * 5})
    assert reading.decision == ComplexityDecision.FLAG_RUNAWAY
    assert reading.scores["chaos"] >= 0.9


def test_suggests_rest_when_hot():
    monitor = ComplexityPressureMonitor(runaway_norm=50.0)
    reading = monitor.evaluate({"state_norm": 35.0, "activity_rate": 0.9,
                                "recent_actions": ["a", "b"] * 10})
    assert reading.decision == ComplexityDecision.SUGGEST_REST


def test_detects_repeated_loop_and_suggests_exploration():
    monitor = ComplexityPressureMonitor()
    reading = monitor.evaluate({
        "recent_actions": ["a"] * 30,
        "state_norm": 2.0, "activity_rate": 0.5, "state_drift": 0.1})
    assert reading.decision == ComplexityDecision.SUGGEST_EXPLORATION
    assert reading.scores["repeated_loop"] >= 0.8
    assert reading.scores["action_diversity"] < 0.1


def test_suggests_replay_for_habit_overdominance():
    monitor = ComplexityPressureMonitor()
    reading = monitor.evaluate({
        "recent_actions": ["a", "b", "c", "a", "b", "c", "d", "a"],
        "state_norm": 2.0, "activity_rate": 0.5, "state_drift": 0.1,
        "habit_weights": {("p1", "a"): 5.0, ("p2", "b"): 0.2,
                          ("p3", "c"): 0.3}})
    assert reading.decision == ComplexityDecision.SUGGEST_REPLAY
    assert reading.scores["habit_overdominance"] >= 0.8


def test_suggests_consolidation_when_quiet():
    monitor = ComplexityPressureMonitor()
    reading = monitor.evaluate({
        "recent_actions": ["a", "b", "c", "d", "a", "b", "c", "d"],
        "state_norm": 0.5, "activity_rate": 0.05, "state_drift": 0.0})
    assert reading.decision == ComplexityDecision.SUGGEST_CONSOLIDATION


def test_normal_behaviour_no_action():
    monitor = ComplexityPressureMonitor()
    reading = monitor.evaluate({
        "recent_actions": ["a", "b", "c", "d", "b", "a", "c", "d", "a"],
        "recent_signal_kinds": ["Stimulus", "Reaction", "Push"],
        "state_norm": 2.0, "activity_rate": 0.5, "state_drift": 0.05})
    assert reading.decision == ComplexityDecision.NO_ACTION


def test_suggestions_are_internal_only():
    """The monitor returns suggestions; it has no way to act on anything."""
    import inspect

    from solaris_ai_nn.latent import complexity_pressure

    source = inspect.getsource(complexity_pressure)
    for forbidden in ("bridge.process", "execute", "subprocess",
                      ".react(", "publish"):
        assert forbidden not in source, forbidden
    reading = ComplexityPressureMonitor().evaluate({})
    assert reading.decision in ComplexityDecision.ALL
    assert reading.reasons  # every decision is explained
