"""Tests for the valence estimator (feedback polarity, not emotion)."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.valence import ValenceEstimator


def test_positive_reaction_increases_rolling_valence():
    estimator = ValenceEstimator()
    assert estimator.rolling() == 0.0
    for _ in range(5):
        estimator.observe("reaction", value=1.0)
    assert estimator.rolling() == 1.0
    assert estimator.current() == 1.0


def test_blocked_action_decreases_valence():
    estimator = ValenceEstimator()
    estimator.observe("reaction", value=0.5)
    before = estimator.rolling()
    estimator.observe("blocked_action")
    estimator.observe("blocked_action")
    assert estimator.rolling() < before
    assert estimator.evidence[-1]["kind"] == "blocked_action"
    assert estimator.evidence[-1]["polarity"] == -0.3


def test_checkpoint_affects_valence():
    estimator = ValenceEstimator()
    estimator.observe("checkpoint_ok")
    assert estimator.current() > 0
    estimator.observe("checkpoint_failed")
    assert estimator.current() < 0
    estimator.observe("restart_gap")
    assert estimator.rolling() < 0


def test_trend_and_confidence():
    estimator = ValenceEstimator()
    for _ in range(6):
        estimator.observe("reaction", value=-0.5)
    for _ in range(6):
        estimator.observe("reaction", value=0.8)
    assert estimator.trend() == "rising"
    assert 0 < estimator.confidence() < 0.95
    state = estimator.state()
    assert state.event_count == 12
    assert state.note == "valence is feedback polarity, not emotion"


def test_values_clamped_and_window_bounded():
    estimator = ValenceEstimator(window=10)
    polarity = estimator.observe("reaction", value=5.0)
    assert polarity == 1.0
    for i in range(30):
        estimator.observe("reaction", value=0.1)
    assert len(estimator._values) == 10


def test_all_spec_sources_recognized():
    from solaris_ai_nn.homeostasis.valence import EVENT_POLARITY

    for kind in ("reward", "danger", "safety_violation", "prediction_hit",
                 "prediction_miss", "checkpoint_ok", "restart_gap",
                 "operator_approval", "operator_rejection",
                 "energy_recovered", "blocked_action", "mysterium_drop",
                 "mysterium_rise"):
        assert kind in EVENT_POLARITY, kind
