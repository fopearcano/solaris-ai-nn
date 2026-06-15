"""Source attribution -- where did a record come from, with uncertainty preserved.

The :class:`SourceAttributionEngine` attributes a record to an external source,
feeder artifact, receptor transformation, internal memory/prediction, simulation,
human annotation, corrupted source, or unknown. Uncertainty is preserved, a
corrupted source never becomes internal truth, and a human-readable gloss never
becomes source evidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class AttributionTarget:
    EXTERNAL_SOURCE = "external_source"
    FEEDER_ARTIFACT = "feeder_artifact"
    RECEPTOR_TRANSFORMATION = "receptor_transformation"
    INTERNAL_MEMORY = "internal_memory"
    INTERNAL_PREDICTION = "internal_prediction"
    SIMULATION = "simulation"
    HUMAN_ANNOTATION = "human_annotation"
    CORRUPTED_SOURCE = "corrupted_source"
    UNKNOWN = "unknown"

    ALL = (EXTERNAL_SOURCE, FEEDER_ARTIFACT, RECEPTOR_TRANSFORMATION,
           INTERNAL_MEMORY, INTERNAL_PREDICTION, SIMULATION, HUMAN_ANNOTATION,
           CORRUPTED_SOURCE, UNKNOWN)


@dataclass
class AttributionEvidence:
    kind: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SourceAttribution:
    """One source attribution (uncertainty preserved; corruption flagged)."""

    target: str
    ref: str
    attribution_id: str = field(
        default_factory=lambda: f"SRC_{uuid.uuid4().hex[:8]}")
    confidence: float = 0.0
    uncertainty: float = 0.0
    corrupted: bool = False
    gloss_is_not_evidence: bool = True
    evidence: List[AttributionEvidence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribution_id": self.attribution_id,
            "target": self.target,
            "ref": self.ref,
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "corrupted": self.corrupted,
            "gloss_is_not_evidence": self.gloss_is_not_evidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "note": "source attribution preserves uncertainty; corrupted source "
                    "is not internal truth; gloss is not source evidence",
        }


@dataclass
class SourceAttributionEngine:
    """Attributes records to sources, preserving uncertainty and corruption."""

    attributions: List[SourceAttribution] = field(default_factory=list)

    def attribute(self, target: str, ref: str, *, confidence: float = 0.5,
                  corrupted: bool = False,
                  evidence: List[AttributionEvidence] = None,
                  ) -> SourceAttribution:
        if target not in AttributionTarget.ALL:
            target = AttributionTarget.UNKNOWN
        # A corrupted source is never promoted to high confidence internal truth.
        if corrupted:
            target = AttributionTarget.CORRUPTED_SOURCE
            confidence = min(confidence, 0.3)
        att = SourceAttribution(
            target=target, ref=ref, confidence=confidence,
            uncertainty=round(1.0 - confidence, 4), corrupted=corrupted,
            evidence=list(evidence or []))
        self.attributions.append(att)
        return att

    def attribute_gloss(self, ref: str) -> SourceAttribution:
        """A human-readable gloss is recorded but explicitly not source evidence."""
        att = SourceAttribution(
            target=AttributionTarget.HUMAN_ANNOTATION, ref=ref, confidence=0.2,
            uncertainty=0.8, gloss_is_not_evidence=True,
            evidence=[AttributionEvidence(kind="gloss",
                                          detail="debug gloss, not evidence")])
        self.attributions.append(att)
        return att

    def corrupted(self) -> List[SourceAttribution]:
        return [a for a in self.attributions if a.corrupted]

    def uncertainty_score(self) -> float:
        if not self.attributions:
            return 0.0
        return round(sum(a.uncertainty for a in self.attributions)
                     / len(self.attributions), 4)

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, int] = {}
        for a in self.attributions:
            out[a.target] = out.get(a.target, 0) + 1
        return {
            "attribution_count": len(self.attributions),
            "corrupted_count": len(self.corrupted()),
            "uncertainty_score": self.uncertainty_score(),
            "distribution": out,
            "attributions": [a.to_dict() for a in self.attributions],
        }
