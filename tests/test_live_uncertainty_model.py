"""Live uncertainty model: computed; contradiction/missing evidence raise it."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import UncertaintyEstimator


def test_uncertainty_computed():
    s = UncertaintyEstimator().estimate(
        sign_stability=0.8, concept_stability=0.8, source_reliability=0.9,
        source_count=2, modality_count=2, recurrence=6, rhythm_present=True,
        supporting_count=6, counter_count=0)
    assert 0.0 <= s.uncertainty <= 1.0
    assert s.low is True
    assert "uncertainty" in s.to_dict()


def test_contradiction_increases_uncertainty():
    base = UncertaintyEstimator().estimate(
        sign_stability=0.8, concept_stability=0.8, source_count=2,
        modality_count=2, recurrence=6, supporting_count=6, counter_count=0)
    contradicted = UncertaintyEstimator().estimate(
        sign_stability=0.8, concept_stability=0.8, source_count=2,
        modality_count=2, recurrence=6, supporting_count=3, counter_count=6)
    assert contradicted.uncertainty > base.uncertainty


def test_missing_evidence_increases_uncertainty():
    base = UncertaintyEstimator().estimate(
        sign_stability=0.8, concept_stability=0.8, source_count=2,
        modality_count=2, recurrence=6, supporting_count=6)
    missing = UncertaintyEstimator().estimate(
        sign_stability=0.8, concept_stability=0.8, source_count=2,
        modality_count=2, recurrence=6, supporting_count=0,
        missing_evidence=True)
    assert missing.uncertainty > base.uncertainty
    assert missing.low is False
