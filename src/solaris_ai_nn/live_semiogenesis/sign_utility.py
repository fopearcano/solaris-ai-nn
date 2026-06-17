"""Live sign utility -- a sign must do something internally useful, not just name.

:class:`LiveSignUtilityAssessment` scores a sign candidate across many factors
(compression, retrieval, ambiguity reduction, recurrence reference, cross-source and
cross-modality linking, prediction potential, stability, noise/absence resistance,
low label/gloss/operator dependence, low source-artifact risk, concept evidence
strength). Scoring is conservative: merely naming a concept is not enough, a sign
that only mirrors a human label has low or blocked utility, and missing evidence
lowers confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SignUtilityFactor:
    COMPRESSION = "compression_usefulness"
    RETRIEVAL = "retrieval_usefulness"
    AMBIGUITY_REDUCTION = "ambiguity_reduction"
    RECURRENCE_REFERENCE = "recurrence_reference_usefulness"
    CROSS_SOURCE = "cross_source_linking"
    CROSS_MODALITY = "cross_modality_linking"
    PREDICTION = "prediction_potential"
    STABILITY = "stability_across_time"
    NOISE_RESISTANCE = "resistance_to_noise"
    ABSENCE_RESISTANCE = "resistance_to_absence"
    LOW_LABEL = "low_label_dependence"
    LOW_GLOSS = "low_debug_gloss_dependence"
    LOW_OPERATOR = "low_operator_dependence"
    LOW_SOURCE_ARTIFACT = "low_source_artifact_risk"
    CONCEPT_EVIDENCE = "concept_evidence_strength"

    ALL = (COMPRESSION, RETRIEVAL, AMBIGUITY_REDUCTION, RECURRENCE_REFERENCE,
           CROSS_SOURCE, CROSS_MODALITY, PREDICTION, STABILITY, NOISE_RESISTANCE,
           ABSENCE_RESISTANCE, LOW_LABEL, LOW_GLOSS, LOW_OPERATOR,
           LOW_SOURCE_ARTIFACT, CONCEPT_EVIDENCE)

_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")


@dataclass
class SignUtilityScore:
    """The conservative utility score for one sign candidate."""

    sign_id: str
    score: float = 0.0
    factors: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @property
    def useful(self) -> bool:
        return self.score >= 0.6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id, "utility_score": round(self.score, 3),
            "useful": self.useful,
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "notes": list(self.notes),
            "note": "a sign must do something internally useful; merely naming a "
                    "concept is not enough; a label-mirroring sign has low or "
                    "blocked utility; missing evidence lowers confidence",
        }


@dataclass
class LiveSignUtilityAssessment:
    """Assesses the internal utility of a sign candidate (conservative)."""

    def assess(self, *, candidate, concept_stability: float = 0.0,
               concept_recurrence: int = 0, load_status: str = "",
               ) -> SignUtilityScore:
        s = SignUtilityScore(sign_id=candidate.sign_id)
        f = s.factors
        total = max(1, sum(candidate.source_distribution.values()) or
                    concept_recurrence)

        f[SignUtilityFactor.COMPRESSION] = min(1.0, concept_recurrence / 6.0)
        f[SignUtilityFactor.RETRIEVAL] = (
            1.0 if candidate.feature_signature_refs else 0.3)
        source_count = len(candidate.source_distribution)
        modality_count = len(candidate.modality_distribution)
        f[SignUtilityFactor.AMBIGUITY_REDUCTION] = (
            0.8 if candidate.feature_signature_refs else 0.3)
        f[SignUtilityFactor.RECURRENCE_REFERENCE] = min(
            1.0, concept_recurrence / 5.0)
        f[SignUtilityFactor.CROSS_SOURCE] = (
            1.0 if source_count >= 2 else 0.4 if source_count == 1 else 0.0)
        f[SignUtilityFactor.CROSS_MODALITY] = (
            1.0 if modality_count >= 2 else 0.4 if modality_count == 1 else 0.0)
        f[SignUtilityFactor.PREDICTION] = min(1.0, concept_recurrence / 8.0)
        f[SignUtilityFactor.STABILITY] = max(0.0, min(1.0, concept_stability))
        f[SignUtilityFactor.NOISE_RESISTANCE] = (
            0.5 if "overload" in str(load_status) else 0.85)
        f[SignUtilityFactor.ABSENCE_RESISTANCE] = (
            0.5 if "deprivation" in str(load_status) else 0.85)

        op_share = candidate.source_distribution.get("operator_pulse", 0) / total
        human_share = sum(candidate.source_distribution.get(s, 0)
                          for s in _HUMAN_TEXT_SOURCES) / total
        label_dep = bool([c for c in candidate.contamination_findings
                          if "label" in c])
        gloss_dep = bool([c for c in candidate.contamination_findings
                          if "gloss" in c])
        f[SignUtilityFactor.LOW_LABEL] = 0.0 if label_dep else max(
            0.0, 1.0 - human_share)
        f[SignUtilityFactor.LOW_GLOSS] = 0.0 if gloss_dep else 1.0
        f[SignUtilityFactor.LOW_OPERATOR] = max(0.0, 1.0 - op_share)
        f[SignUtilityFactor.LOW_SOURCE_ARTIFACT] = (
            0.4 if "source_artifact" in candidate.contamination_findings
            else 1.0)
        f[SignUtilityFactor.CONCEPT_EVIDENCE] = max(0.0, min(
            1.0, concept_stability * 0.5 + min(1.0, concept_recurrence / 6.0)
            * 0.5))

        s.score = sum(f.values()) / len(f) if f else 0.0

        if label_dep:
            s.notes.append("label-dependent; utility blocked toward low")
            s.score = min(s.score, 0.35)
        if op_share >= 0.5:
            s.notes.append("operator-pulse share high; utility capped")
            s.score = min(s.score, 0.4)
        if concept_recurrence < 2:
            s.notes.append("insufficient concept recurrence; low confidence")
            s.score = min(s.score, 0.45)
        if candidate.counter_count > candidate.supporting_count:
            s.notes.append("counterevidence exceeds support; utility lowered")
            s.score = min(s.score, 0.4)
        return s
