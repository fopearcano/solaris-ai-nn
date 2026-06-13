"""Tests for the stagnation detector."""

from __future__ import annotations

from solaris_ai_nn.active_perception.stagnation import (
    StagnationDetector,
    StagnationStatus,
)


def test_detects_flat_growth_with_high_mysterium():
    det = StagnationDetector()
    state = det.detect({"structural_change_score": 0.0,
                        "mysterium_pressure": 0.7,
                        "developmental": {"structural_change_score": 0.0}})
    assert state.status == StagnationStatus.STAGNATING


def test_stable_when_flat_and_calm():
    det = StagnationDetector()
    state = det.detect({"structural_change_score": 0.0,
                        "mysterium_pressure": 0.0,
                        "developmental": {"structural_change_score": 0.0}})
    assert state.status == StagnationStatus.STABLE


def test_overactive_when_racing():
    det = StagnationDetector()
    state = det.detect({"structural_change_score": 0.9,
                        "novelty_rate": 0.8,
                        "developmental": {"structural_change_score": 0.9}})
    assert state.status == StagnationStatus.OVERACTIVE


def test_unknown_without_evidence():
    det = StagnationDetector()
    state = det.detect({})
    assert state.status == StagnationStatus.UNKNOWN


def test_recommends_sampling_pressure():
    det = StagnationDetector()
    assert det.recommend_sampling_pressure(StagnationStatus.INERT) > \
        det.recommend_sampling_pressure(StagnationStatus.STABLE)
    # Overactive should not add pressure.
    assert det.recommend_sampling_pressure(StagnationStatus.OVERACTIVE) == 0.0


def test_inert_distinguished_from_stagnating():
    det = StagnationDetector()
    state = det.detect({"structural_change_score": 0.0,
                        "mysterium_pressure": 0.1,
                        "developmental": {"structural_change_score": 0.0},
                        "world_model_growth_flat": True,
                        "prediction_accuracy_flat": True,
                        "proto_language": {"symbol_count": 5,
                                           "stable_symbol_count": 0}})
    assert state.status in (StagnationStatus.INERT,
                            StagnationStatus.STAGNATING)
