"""Tests for the curiosity (intrinsic pressure) estimator."""

from __future__ import annotations

from solaris_ai_nn.active_perception.curiosity import CuriosityEstimator


def test_unresolved_mysterium_increases_pressure():
    est = CuriosityEstimator()
    low = est.estimate({"mysterium_pressure": 0.0}).pressure
    high = est.estimate({"mysterium_pressure": 0.9}).pressure
    assert high > low


def test_critical_health_reduces_curiosity():
    est = CuriosityEstimator()
    calm = est.estimate({"mysterium_pressure": 0.8}).pressure
    critical = est.estimate({"mysterium_pressure": 0.8,
                             "health_level": "critical"}).pressure
    assert critical < calm


def test_safety_cannot_be_overridden():
    est = CuriosityEstimator()
    state = est.estimate({"mysterium_pressure": 1.0, "novelty_rate": 0.9,
                          "emergency": True})
    assert state.suppressed_by_safety is True
    assert state.pressure <= 0.05


def test_stagnation_raises_curiosity():
    est = CuriosityEstimator()
    base = est.estimate({}).pressure
    stuck = est.estimate({"stagnation_status": "stagnating"}).pressure
    assert stuck > base


def test_exhaustion_damps_curiosity():
    est = CuriosityEstimator()
    rested = est.estimate({"mysterium_pressure": 0.6, "energy": 0.9}).pressure
    tired = est.estimate({"mysterium_pressure": 0.6, "energy": 0.1}).pressure
    assert tired < rested


def test_note_is_not_anthropomorphic():
    est = CuriosityEstimator()
    snap = est.estimate({"mysterium_pressure": 0.5}).to_dict()
    assert "not a desire" in snap["note"]
