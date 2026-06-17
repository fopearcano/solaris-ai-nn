"""Live concept stability scoring -- conservative, evidence-weighted.

:class:`StabilityScorer` scores a proto-concept candidate on multiple factors
(recurrence strength, source/modality diversity, temporal persistence, noise
resistance, absence tolerance, low contamination / operator / label / gloss
dependence, cross-source support, payload consistency, source reliability). Scoring
is deliberately conservative: high recurrence from one noisy source or from operator
text is not enough, missing evidence lowers confidence, and contradictory evidence
lowers confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class StabilityFactor:
    RECURRENCE = "recurrence_strength"
    SOURCE_DIVERSITY = "source_diversity"
    MODALITY_DIVERSITY = "modality_diversity"
    TEMPORAL_PERSISTENCE = "temporal_persistence"
    NOISE_RESISTANCE = "resistance_to_noise"
    ABSENCE_TOLERANCE = "absence_tolerance"
    LOW_CONTAMINATION = "low_contamination_risk"
    LOW_OPERATOR_DOMINANCE = "low_operator_dominance"
    LOW_HUMAN_LABEL = "low_human_label_dependence"
    LOW_DEBUG_GLOSS = "low_debug_gloss_dependence"
    CROSS_SOURCE = "cross_source_support"
    PREDICTION_POTENTIAL = "prediction_potential"
    SOURCE_RELIABILITY = "source_reliability"
    PAYLOAD_CONSISTENCY = "payload_consistency"

    ALL = (RECURRENCE, SOURCE_DIVERSITY, MODALITY_DIVERSITY,
           TEMPORAL_PERSISTENCE, NOISE_RESISTANCE, ABSENCE_TOLERANCE,
           LOW_CONTAMINATION, LOW_OPERATOR_DOMINANCE, LOW_HUMAN_LABEL,
           LOW_DEBUG_GLOSS, CROSS_SOURCE, PREDICTION_POTENTIAL,
           SOURCE_RELIABILITY, PAYLOAD_CONSISTENCY)

_STRENGTH_SCORE = {"strong": 1.0, "moderate": 0.7, "weak": 0.3,
                   "unstable": 0.1, "none": 0.0, "inconclusive": 0.2}


@dataclass
class LiveConceptStabilityScore:
    """The conservative stability score for one candidate."""

    candidate_id: str
    score: float = 0.0
    factors: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @property
    def is_stable(self) -> bool:
        return self.score >= 0.6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id, "stability_score": round(
                self.score, 3),
            "is_stable": self.is_stable,
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "notes": list(self.notes),
            "note": "scoring is conservative; recurrence from one noisy source "
                    "or from operator text is not enough; missing or "
                    "contradictory evidence lowers confidence",
        }


@dataclass
class StabilityScorer:
    """Scores candidate stability across multiple conservative factors."""

    def score(self, *, candidate, recurrence_strength: str,
              source_reliability: float = 0.7) -> LiveConceptStabilityScore:
        s = LiveConceptStabilityScore(candidate_id=candidate.candidate_id)
        f = s.factors

        f[StabilityFactor.RECURRENCE] = _STRENGTH_SCORE.get(
            recurrence_strength, 0.0)
        f[StabilityFactor.SOURCE_DIVERSITY] = min(
            1.0, (candidate.source_count - 1) / 2.0) \
            if candidate.source_count else 0.0
        f[StabilityFactor.MODALITY_DIVERSITY] = min(
            1.0, (len(candidate.modality_distribution) - 1) / 2.0) \
            if candidate.modality_distribution else 0.0
        f[StabilityFactor.TEMPORAL_PERSISTENCE] = (
            1.0 if candidate.first_seen and candidate.last_seen
            and candidate.first_seen != candidate.last_seen else 0.4)

        total = max(1, candidate.recurrence_count)
        noisy_support = sum(1 for e in candidate.supporting_events
                            if "noisy" in (e.detail or ""))
        f[StabilityFactor.NOISE_RESISTANCE] = max(
            0.0, 1.0 - noisy_support / total)
        f[StabilityFactor.ABSENCE_TOLERANCE] = (
            0.8 if candidate.absence_windows == 0 else 0.5)

        contaminated = bool(candidate.contamination_findings)
        f[StabilityFactor.LOW_CONTAMINATION] = 0.0 if contaminated else 1.0

        op_share = (candidate.source_distribution.get("operator_pulse", 0)
                    / total)
        f[StabilityFactor.LOW_OPERATOR_DOMINANCE] = max(0.0, 1.0 - op_share)
        human_share = sum(candidate.source_distribution.get(s, 0)
                          for s in ("operator_pulse",
                                    "local_environment_manual")) / total
        f[StabilityFactor.LOW_HUMAN_LABEL] = max(0.0, 1.0 - human_share)
        # Debug gloss is never ground truth -> dependence is structurally zero.
        f[StabilityFactor.LOW_DEBUG_GLOSS] = 1.0
        f[StabilityFactor.CROSS_SOURCE] = (
            1.0 if candidate.source_count >= 2 else 0.0)
        f[StabilityFactor.PREDICTION_POTENTIAL] = min(
            1.0, candidate.recurrence_count / 10.0)
        f[StabilityFactor.SOURCE_RELIABILITY] = max(0.0, min(
            1.0, source_reliability))

        # Payload consistency: counterevidence lowers it.
        f[StabilityFactor.PAYLOAD_CONSISTENCY] = max(
            0.0, 1.0 - candidate.counter_count / total)

        s.score = sum(f.values()) / len(f) if f else 0.0

        if op_share >= 0.5:
            s.notes.append("operator-pulse share high; stability capped")
            s.score = min(s.score, 0.45)
        if recurrence_strength in ("none", "weak", "unstable"):
            s.notes.append("weak/unstable recurrence; stability capped")
            s.score = min(s.score, 0.5)
        if candidate.counter_count > candidate.supporting_count:
            s.notes.append("counterevidence exceeds support; stability lowered")
            s.score = min(s.score, 0.4)
        if contaminated:
            s.notes.append("contamination present; stability lowered")
            s.score = min(s.score, 0.3)
        return s
