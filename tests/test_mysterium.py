"""Tests for the Mysterium (unknown pressure) tracker."""

from __future__ import annotations

from solaris_ai_nn.latent.mysterium import MysteriumTracker


def test_pressure_increases_with_misses_and_novelty():
    tracker = MysteriumTracker(pressure=0.2)
    before = tracker.pressure
    tracker.update({"prediction_miss_streak": 5, "novelty": 0.9,
                    "unexplained_error": 0.8, "logos_fracture": 0.7})
    assert tracker.pressure > before
    tracker.update({"replay_mismatch": True, "blocked_actions": 2,
                    "counterfactual_divergence": 0.9,
                    "low_trace_coverage": True})
    assert tracker.pressure > before + 0.1


def test_pressure_decreases_with_successful_prediction():
    tracker = MysteriumTracker(pressure=0.6)
    before = tracker.pressure
    tracker.update({"prediction_hit": True, "stable_patterns": True,
                    "consolidated": True, "reduced_error": True,
                    "replay_reproduced": True})
    assert tracker.pressure < before


def test_pressure_clamped_to_unit_interval():
    tracker = MysteriumTracker(pressure=0.95)
    for _ in range(20):
        tracker.increase("test", 0.5)
    assert tracker.pressure == 1.0
    for _ in range(20):
        tracker.decrease("test", 0.5)
    assert tracker.pressure == 0.0


def test_reasons_recorded():
    tracker = MysteriumTracker()
    tracker.increase("replay failed to reproduce", 0.06)
    tracker.decrease("memory was consolidated", 0.04)
    assert len(tracker.reasons) == 2
    assert tracker.reasons[0]["delta"] > 0
    assert tracker.reasons[1]["delta"] < 0
    assert all("reason" in r and "pressure" in r for r in tracker.reasons)
    state = tracker.update({"novelty": 0.9})
    assert state.top_reasons
    assert state.level in ("low", "elevated", "high")
    assert state.trend in ("rising", "falling", "stable")


def test_levels_and_trend():
    tracker = MysteriumTracker(pressure=0.1)
    assert tracker.level() == "low"
    tracker.pressure = 0.5
    assert tracker.level() == "elevated"
    tracker.pressure = 0.8
    assert tracker.level() == "high"
    for _ in range(6):
        tracker.update({"novelty": 0.9})
    assert tracker.trend() in ("rising", "stable")  # rising until clamped


def test_not_presented_as_mystical():
    tracker = MysteriumTracker()
    snap = tracker.snapshot()
    assert "numeric unknown-pressure estimate" in snap["note"]
    assert "nothing mystical" in snap["note"]
    # And the module's own docs keep the framing honest.
    import inspect

    from solaris_ai_nn.latent import mysterium

    doc = inspect.getdoc(mysterium)
    assert "numeric" in doc.lower()
