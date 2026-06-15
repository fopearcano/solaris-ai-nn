"""Grounding -- operational association from features, not human understanding.

A :class:`SensoriumGroundingAnalyzer` scores how well a candidate structure is
*grounded* in the sensorium: repeated field patterns, cross-time persistence,
predictive/compression usefulness, cross-modal relations, and -- crucially -- low
dependence on human labels. Strong grounding must rest on feature patterns with
preserved provenance, not on semantic labels; human-label contamination is
tracked explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class GroundingQuality:
    UNSUPPORTED = "unsupported"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    AMBIGUOUS = "ambiguous"
    OVERFIT_TO_FIXTURE = "overfit_to_fixture"
    HUMAN_LABEL_CONTAMINATED = "human_label_contaminated"
    MODALITY_NATIVE = "modality_native"

    ALL = (UNSUPPORTED, WEAK, MODERATE, STRONG, AMBIGUOUS, OVERFIT_TO_FIXTURE,
           HUMAN_LABEL_CONTAMINATED, MODALITY_NATIVE)


@dataclass
class SensoriumGroundingRecord:
    """A grounding assessment for one candidate structure."""

    candidate_id: str
    modality: str
    quality: str
    score: float
    criteria_met: List[str] = field(default_factory=list)
    human_label_dependence: float = 0.0
    provenance_preserved: bool = True
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoriumGroundingAnalyzer:
    """Scores grounding from feature evidence, penalising human-label reliance."""

    records: List[SensoriumGroundingRecord] = field(default_factory=list)

    def assess(self, *, candidate_id: str, modality: str,
               repeated_pattern: bool = False,
               cross_time_persistence: bool = False,
               predictive_useful: bool = False,
               compression_useful: bool = False,
               cross_modal_relation: bool = False,
               absence_prediction: bool = False,
               provenance_preserved: bool = True,
               human_label_dependence: float = 0.0,
               external_uncertainty: bool = True,
               fixture_only: bool = False) -> SensoriumGroundingRecord:
        criteria: List[str] = []
        if repeated_pattern:
            criteria.append("repeated_field_pattern")
        if cross_time_persistence:
            criteria.append("cross_time_persistence")
        if predictive_useful:
            criteria.append("predictive_usefulness")
        if compression_useful:
            criteria.append("compression_usefulness")
        if cross_modal_relation:
            criteria.append("cross_modal_relation")
        if absence_prediction:
            criteria.append("successful_absence_prediction")
        if human_label_dependence < 0.2:
            criteria.append("low_human_label_dependence")
        if provenance_preserved:
            criteria.append("preserved_provenance")
        if external_uncertainty:
            criteria.append("external_uncertainty_present")

        score = len(criteria) / 9.0
        notes: List[str] = []

        # Classify quality. Human-label contamination and fixture overfit are
        # named explicitly and cap the quality.
        if human_label_dependence >= 0.5:
            quality = GroundingQuality.HUMAN_LABEL_CONTAMINATED
            notes.append("grounding leans on human labels; not modality-native")
        elif fixture_only and not cross_time_persistence:
            quality = GroundingQuality.OVERFIT_TO_FIXTURE
            notes.append("pattern seen only in fixture; may not generalise")
        elif not provenance_preserved:
            quality = GroundingQuality.AMBIGUOUS
            notes.append("provenance not preserved; association is ambiguous")
        elif score >= 0.7 and human_label_dependence < 0.2:
            quality = GroundingQuality.MODALITY_NATIVE
        elif score >= 0.55:
            quality = GroundingQuality.STRONG
        elif score >= 0.35:
            quality = GroundingQuality.MODERATE
        elif score > 0.0:
            quality = GroundingQuality.WEAK
        else:
            quality = GroundingQuality.UNSUPPORTED

        record = SensoriumGroundingRecord(
            candidate_id=candidate_id, modality=modality, quality=quality,
            score=round(score, 3), criteria_met=criteria,
            human_label_dependence=human_label_dependence,
            provenance_preserved=provenance_preserved, notes=notes)
        self.records.append(record)
        return record

    def human_label_contamination_score(self) -> float:
        """Fraction of assessed candidates that lean on human labels."""
        if not self.records:
            return 0.0
        contaminated = sum(
            1 for r in self.records
            if r.quality == GroundingQuality.HUMAN_LABEL_CONTAMINATED
            or r.human_label_dependence >= 0.5)
        return round(contaminated / len(self.records), 3)

    def modality_native_grounding_score(self) -> float:
        """Fraction of assessed candidates grounded in modality-native features."""
        if not self.records:
            return 0.0
        native = sum(1 for r in self.records
                     if r.quality in (GroundingQuality.MODALITY_NATIVE,
                                      GroundingQuality.STRONG))
        return round(native / len(self.records), 3)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "grounding_record_count": len(self.records),
            "human_label_contamination_score":
                self.human_label_contamination_score(),
            "modality_native_grounding_score":
                self.modality_native_grounding_score(),
            "records": [r.to_dict() for r in self.records],
        }
