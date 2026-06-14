"""Pilot-2 <-> Post-Pilot: nursery vs sensory comparison + classification."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import (
    SensoryExposureClassification,
    classify_sensory_exposure,
)


def test_nursery_vs_sensory_comparison_runs():
    result = classify_sensory_exposure(
        {"symbol_stability": 0.5, "prediction_score": 0.4,
         "ambiguity_ratio": 0.4},
        {"symbol_stability": 0.58, "prediction_score": 0.5,
         "ambiguity_ratio": 0.32, "grounding_quality": "moderate"})
    assert result.classification == \
        SensoryExposureClassification.IMPROVED_GROUNDING
    assert result.observed_differences


def test_sensory_exposure_inconclusive_if_artifacts_missing():
    result = classify_sensory_exposure(None, {"symbol_stability": 0.6})
    assert result.classification == \
        SensoryExposureClassification.INCONCLUSIVE


def test_overload_classified():
    result = classify_sensory_exposure(
        {"symbol_stability": 0.5},
        {"symbol_stability": 0.5, "malformed_event_rate": 0.8,
         "overload_signal": True})
    assert result.classification == \
        SensoryExposureClassification.CAUSED_OVERLOAD


def test_noise_only_classified():
    result = classify_sensory_exposure(
        {"symbol_stability": 0.6, "prediction_score": 0.6},
        {"symbol_stability": 0.5, "prediction_score": 0.5})
    assert result.classification == \
        SensoryExposureClassification.ADDED_NOISE_ONLY


def test_no_causal_or_consciousness_claim():
    result = classify_sensory_exposure(
        {"symbol_stability": 0.5}, {"symbol_stability": 0.6})
    assert "not proven causal" in result.disclaimer
    assert "consciousness" in result.disclaimer
