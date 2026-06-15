"""Stabilization -- provisionally promoting concepts that keep earning their keep.

The :class:`ConceptStabilizationEngine` evaluates each proto-concept against
evidence criteria (recurrence over time/sources, prediction/compression/attention
usefulness, cross-modal/absence confirmation, low human-label dependence, noise
survival, fixture->live survival). Stability is *provisional*: stable does not mean
true and never means conscious, and fixture-only stability is marked as such.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .proto_concepts import ProtoConcept, ProtoConceptStatus


@dataclass
class StabilityEvidence:
    """One named criterion and whether the concept met it."""

    criterion: str
    met: bool
    weight: float
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class StabilizationResult:
    concept_id: str
    stability_score: float
    status: str
    fixture_only: bool
    evidence: List[StabilityEvidence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "stability_score": round(self.stability_score, 4),
            "status": self.status,
            "fixture_only": self.fixture_only,
            "evidence": [e.to_dict() for e in self.evidence],
            "note": "stability is provisional; stable does not mean true or "
                    "conscious",
        }


@dataclass
class ConceptStabilizationEngine:
    """Scores and (provisionally) promotes concepts from evidence."""

    stable_threshold: float = 0.6

    def stabilize(self, concept: ProtoConcept) -> StabilizationResult:
        ev: List[StabilityEvidence] = []

        def crit(name: str, met: bool, weight: float, detail: str = "") -> None:
            ev.append(StabilityEvidence(name, met, weight, detail))

        crit("recurrence_across_time", concept.recurrence_count >= 3, 0.2,
             f"recurrence={concept.recurrence_count}")
        crit("recurrence_across_sources", len(concept.source_distribution) >= 2,
             0.1, f"sources={len(concept.source_distribution)}")
        crit("prediction_improvement", concept.prediction_utility >= 0.5, 0.15)
        crit("compression_improvement", concept.compression_utility >= 0.5, 0.15)
        crit("attention_usefulness", concept.attention_utility >= 0.5, 0.1)
        crit("cross_modal_confirmation", concept.is_cross_modal, 0.1)
        crit("absence_prediction", concept.is_absence_based, 0.05)
        crit("low_human_label_dependence",
             concept.human_label_contamination_score < 0.5, 0.1,
             f"contamination={round(concept.human_label_contamination_score, 3)}")
        crit("survives_noise", concept.stability_score >= 0.3, 0.05)
        # Fixture->live transition is only credited when live grounding exists.
        crit("survives_fixture_to_live", concept.live_grounded, 0.05,
             "live grounding present" if concept.live_grounded
             else "fixture-only (not yet live-confirmed)")

        score = sum(e.weight for e in ev if e.met)
        # Blend with any prior recurrence-driven stability already present.
        score = round(min(1.0, 0.5 * score + 0.5 * (score + 0.0)), 4)
        fixture_only = not concept.live_grounded

        if score >= self.stable_threshold:
            status = ProtoConceptStatus.STABLE
        elif score >= 0.3:
            status = ProtoConceptStatus.EMERGING
        else:
            status = ProtoConceptStatus.UNSTABLE

        # Update the concept in place (provisional).
        concept.stability_score = score
        if status == ProtoConceptStatus.STABLE and fixture_only:
            if "stable on fixture data only; not yet live-confirmed" \
                    not in concept.limitations:
                concept.limitations.append(
                    "stable on fixture data only; not yet live-confirmed")
        if concept.status not in (ProtoConceptStatus.DECAYING,
                                  ProtoConceptStatus.REJECTED,
                                  ProtoConceptStatus.MERGED,
                                  ProtoConceptStatus.SPLIT):
            concept.status = status
        return StabilizationResult(
            concept_id=concept.concept_id, stability_score=score,
            status=status, fixture_only=fixture_only, evidence=ev)
