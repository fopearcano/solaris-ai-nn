"""Boundary state -- the operational zones of self vs world (not a subjective self).

:class:`SelfBoundaryState` tracks which :class:`BoundaryZone` a record belongs to
(internal state, receptor body, sensory membrane, external feeder/world source,
memory, prediction, simulation, counterfactual, operator annotation, unknown) and
how confident that assignment is. Boundary uncertainty is explicitly allowed. This
is an operational self/world boundary, NOT a subjective self and NOT personhood.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class BoundaryZone:
    INTERNAL_STATE = "internal_state"
    RECEPTOR_BODY = "receptor_body"
    SENSORY_MEMBRANE = "sensory_membrane"
    EXTERNAL_FEEDER = "external_feeder"
    EXTERNAL_WORLD_SOURCE = "external_world_source"
    MEMORY_TRACE = "memory_trace"
    PREDICTION = "prediction"
    SIMULATION = "simulation"
    COUNTERFACTUAL = "counterfactual"
    OPERATOR_ANNOTATION = "operator_annotation"
    UNKNOWN = "unknown"

    ALL = (INTERNAL_STATE, RECEPTOR_BODY, SENSORY_MEMBRANE, EXTERNAL_FEEDER,
           EXTERNAL_WORLD_SOURCE, MEMORY_TRACE, PREDICTION, SIMULATION,
           COUNTERFACTUAL, OPERATOR_ANNOTATION, UNKNOWN)

    # Zones that are part of Solaris' operational "self" side of the boundary.
    SELF_SIDE = frozenset({INTERNAL_STATE, RECEPTOR_BODY, SENSORY_MEMBRANE})
    # Zones that are clearly on the "world" side.
    WORLD_SIDE = frozenset({EXTERNAL_FEEDER, EXTERNAL_WORLD_SOURCE})


class BoundaryConfidence:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

    ALL = (LOW, MODERATE, HIGH)

    @staticmethod
    def band(score: float) -> str:
        if score >= 0.66:
            return BoundaryConfidence.HIGH
        if score >= 0.33:
            return BoundaryConfidence.MODERATE
        return BoundaryConfidence.LOW


@dataclass
class BoundaryEvent:
    """One operational assignment of a record to a boundary zone."""

    zone: str
    ref: str
    event_id: str = field(default_factory=lambda: f"BND_{uuid.uuid4().hex[:8]}")
    confidence: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def confidence_band(self) -> str:
        return BoundaryConfidence.band(self.confidence)

    @property
    def uncertain(self) -> bool:
        return self.zone == BoundaryZone.UNKNOWN or self.confidence < 0.33

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "zone": self.zone,
            "ref": self.ref,
            "confidence": round(self.confidence, 4),
            "confidence_band": self.confidence_band,
            "uncertain": self.uncertain,
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
            "note": "operational boundary assignment; not a subjective self",
        }


@dataclass
class SelfBoundaryState:
    """The set of boundary assignments this tick (uncertainty allowed)."""

    events: List[BoundaryEvent] = field(default_factory=list)

    def add(self, zone: str, ref: str, confidence: float,
            evidence_refs: List[str] = None) -> BoundaryEvent:
        if zone not in BoundaryZone.ALL:
            zone = BoundaryZone.UNKNOWN
        ev = BoundaryEvent(zone=zone, ref=ref, confidence=confidence,
                           evidence_refs=list(evidence_refs or []))
        self.events.append(ev)
        return ev

    def zone_distribution(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.events:
            out[e.zone] = out.get(e.zone, 0) + 1
        return out

    def confidence_score(self) -> float:
        if not self.events:
            return 0.0
        return round(sum(e.confidence for e in self.events)
                     / len(self.events), 4)

    def unknown_count(self) -> int:
        return sum(1 for e in self.events if e.zone == BoundaryZone.UNKNOWN)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_count": len(self.events),
            "zone_distribution": self.zone_distribution(),
            "boundary_confidence_score": self.confidence_score(),
            "unknown_count": self.unknown_count(),
            "events": [e.to_dict() for e in self.events],
            "note": "operational self/world boundary; NOT subjective selfhood, "
                    "NOT personhood, NOT a metaphysical claim",
        }
