"""SensoriumGroundingAnalyzer: feature grounding; label contamination tracked."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import GroundingQuality, SensoriumGroundingAnalyzer


def test_feature_evidence_grounds_symbol():
    an = SensoriumGroundingAnalyzer()
    rec = an.assess(candidate_id="c1", modality="radio_frequency",
                    repeated_pattern=True, cross_time_persistence=True,
                    predictive_useful=True, compression_useful=True,
                    cross_modal_relation=True, provenance_preserved=True,
                    human_label_dependence=0.0)
    assert rec.quality in (GroundingQuality.MODALITY_NATIVE,
                           GroundingQuality.STRONG)
    assert rec.score > 0.5


def test_human_label_contamination_detected():
    an = SensoriumGroundingAnalyzer()
    rec = an.assess(candidate_id="c2", modality="human_textual",
                    repeated_pattern=True, human_label_dependence=0.8)
    assert rec.quality == GroundingQuality.HUMAN_LABEL_CONTAMINATED
    assert an.human_label_contamination_score() > 0.0


def test_strong_grounding_requires_provenance():
    an = SensoriumGroundingAnalyzer()
    rec = an.assess(candidate_id="c3", modality="radio_frequency",
                    repeated_pattern=True, cross_time_persistence=True,
                    predictive_useful=True, provenance_preserved=False,
                    human_label_dependence=0.0)
    # Without preserved provenance, grounding is ambiguous, never strong.
    assert rec.quality == GroundingQuality.AMBIGUOUS


def test_fixture_only_flagged_as_overfit():
    an = SensoriumGroundingAnalyzer()
    rec = an.assess(candidate_id="c4", modality="radio_frequency",
                    repeated_pattern=True, cross_time_persistence=False,
                    human_label_dependence=0.0, fixture_only=True)
    assert rec.quality == GroundingQuality.OVERFIT_TO_FIXTURE
