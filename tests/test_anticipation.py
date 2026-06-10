"""Tests for the anticipation tracker."""

from __future__ import annotations

from solaris_ai_nn.latent.anticipation import (
    AnticipationTracker,
    valence_bucket,
)


def _steady(tracker, n, kind="Stimulus", action="a", valence=1.0):
    for _ in range(n):
        tracker.predict({})
        tracker.observe_actual({"input_type": kind,
                                "suggested_action": action,
                                "valence": valence, "is_absence": False,
                                "reservoir_energy": 1.0})


def test_prediction_recorded():
    tracker = AnticipationTracker()
    _steady(tracker, 3)
    prediction = tracker.predict({})
    assert prediction.next_signal_kind == "Stimulus"
    assert prediction.next_action == "a"
    assert prediction.next_valence_bucket == "positive"
    assert prediction.activity_trend in ("rising", "falling", "stable")
    assert prediction.basis["observations"] > 0


def test_hit_and_miss_scored():
    tracker = AnticipationTracker()
    _steady(tracker, 10)
    # A matching observation scores a hit...
    tracker.predict({})
    score = tracker.observe_actual({"input_type": "Stimulus",
                                    "suggested_action": "a", "valence": 1.0,
                                    "is_absence": False})
    assert score["hit"] is True
    assert tracker.miss_streak == 0
    # ...and a contradicting one scores a miss.
    tracker.predict({})
    score = tracker.observe_actual({"input_type": "LogosTension",
                                    "suggested_action": "b",
                                    "valence": -1.0, "is_absence": True})
    assert score["hit"] is False
    assert tracker.miss_streak == 1
    assert tracker.hit_count >= 1 and tracker.miss_count >= 1
    assert tracker.prediction_count == tracker.hit_count + tracker.miss_count


def test_rolling_accuracy_computed():
    tracker = AnticipationTracker(rolling_window=20)
    _steady(tracker, 30)
    assert tracker.rolling_accuracy() > 0.9
    # Sustained surprise drives accuracy down and surprise up.
    for i in range(20):
        tracker.predict({})
        tracker.observe_actual({"input_type": ["Push", "Reaction"][i % 2],
                                "suggested_action": ["b", "c"][i % 2],
                                "valence": -1.0, "is_absence": True})
    assert tracker.rolling_accuracy() < 0.6
    assert tracker.surprise_estimate() > 0.3
    assert 0.0 <= tracker.anticipation_loss() <= 1.0


def test_absence_probability_tracks_rate():
    tracker = AnticipationTracker()
    for i in range(20):
        tracker.observe_actual({"input_type": "Stimulus",
                                "is_absence": i % 2 == 0})
    prediction = tracker.predict({})
    assert 0.4 <= prediction.absence_probability <= 0.6


def test_snapshot_has_all_metrics():
    tracker = AnticipationTracker()
    _steady(tracker, 5)
    snap = tracker.snapshot()
    for key in ("prediction_count", "hit_count", "miss_count",
                "rolling_accuracy", "miss_streak", "surprise_estimate",
                "anticipation_loss", "last_score"):
        assert key in snap, key


def test_valence_buckets():
    assert valence_bucket(0.8) == "positive"
    assert valence_bucket(-0.8) == "negative"
    assert valence_bucket(0.05) == "neutral"
    assert valence_bucket(None) == "none"


def test_no_deep_learning():
    """The tracker is frequency/recency statistics; no ML frameworks."""
    import inspect

    from solaris_ai_nn.latent import anticipation

    source = inspect.getsource(anticipation)
    for forbidden in ("torch", "tensorflow", "jax", "sklearn", "keras"):
        assert forbidden not in source, forbidden
