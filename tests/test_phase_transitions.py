"""Tests for phase transition detection."""

from __future__ import annotations

from solaris_ai_nn.developmental.phase_transitions import (
    PhaseTransitionDetector,
)


def test_phase_transition_candidate_generated():
    detector = PhaseTransitionDetector()
    detector.observe({"prediction_accuracy": 0.4})
    candidates = detector.observe({"prediction_accuracy": 0.8})
    assert candidates
    assert candidates[0].kind == "prediction_accuracy_jump"
    assert len(detector.candidates) == 1
    # Mysterium spike and drop both detected.
    detector2 = PhaseTransitionDetector()
    detector2.observe({"mysterium_pressure": 0.2})
    spike = detector2.observe({"mysterium_pressure": 0.8})
    assert spike[0].kind == "mysterium_spike"


def test_before_after_metrics_included():
    detector = PhaseTransitionDetector()
    detector.observe({"prediction_accuracy": 0.4})
    candidate = detector.observe({"prediction_accuracy": 0.8})[0]
    assert candidate.before == 0.4
    assert candidate.after == 0.8
    assert candidate.delta == 0.4
    assert candidate.metric == "prediction_accuracy"


def test_confidence_exposed_and_capped():
    detector = PhaseTransitionDetector()
    detector.observe({"prediction_accuracy": 0.0})
    candidate = detector.observe({"prediction_accuracy": 1.0})[0]
    assert 0 < candidate.confidence <= 0.8  # never certainty


def test_no_emergence_overclaim():
    detector = PhaseTransitionDetector()
    detector.observe({"mysterium_pressure": 0.9})
    candidate = detector.observe({"mysterium_pressure": 0.2})[0]
    assert "hypothesis" in candidate.note
    assert "not proof of emergence" in candidate.note
    assert "not proof" in detector.snapshot()["note"]


def test_small_moves_are_not_candidates():
    detector = PhaseTransitionDetector()
    detector.observe({"prediction_accuracy": 0.50})
    assert detector.observe({"prediction_accuracy": 0.55}) == []
