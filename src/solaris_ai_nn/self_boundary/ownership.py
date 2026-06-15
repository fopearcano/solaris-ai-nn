"""Ownership attribution -- whose event is this (self / world / sim / memory)?

The :class:`OwnershipAttributor` decides whether an event belongs to Solaris'
internal state, its receptor body, an external source/feeder, a report/debug layer,
an internal simulation, or a remembered trace. Sensory input is NOT "self" merely
because Solaris processed it; internal simulation is NOT the real world; operator
annotation is NOT ground truth; and failed/ambiguous attribution is preserved.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .boundary_state import BoundaryZone


class OwnershipType:
    SELF_INTERNAL = "self_internal"
    SELF_RECEPTOR_STATE = "self_receptor_state"
    EXTERNAL_SOURCE = "external_source"
    EXTERNAL_FEEDER_ARTIFACT = "external_feeder_artifact"
    OPERATOR_ANNOTATION = "operator_annotation"
    MEMORY_REPLAY = "memory_replay"
    INTERNAL_SIMULATION = "internal_simulation"
    COUNTERFACTUAL = "counterfactual"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"

    ALL = (SELF_INTERNAL, SELF_RECEPTOR_STATE, EXTERNAL_SOURCE,
           EXTERNAL_FEEDER_ARTIFACT, OPERATOR_ANNOTATION, MEMORY_REPLAY,
           INTERNAL_SIMULATION, COUNTERFACTUAL, AMBIGUOUS, UNKNOWN)


_OWNERSHIP_TO_ZONE = {
    OwnershipType.SELF_INTERNAL: BoundaryZone.INTERNAL_STATE,
    OwnershipType.SELF_RECEPTOR_STATE: BoundaryZone.RECEPTOR_BODY,
    OwnershipType.EXTERNAL_SOURCE: BoundaryZone.EXTERNAL_WORLD_SOURCE,
    OwnershipType.EXTERNAL_FEEDER_ARTIFACT: BoundaryZone.EXTERNAL_FEEDER,
    OwnershipType.OPERATOR_ANNOTATION: BoundaryZone.OPERATOR_ANNOTATION,
    OwnershipType.MEMORY_REPLAY: BoundaryZone.MEMORY_TRACE,
    OwnershipType.INTERNAL_SIMULATION: BoundaryZone.SIMULATION,
    OwnershipType.COUNTERFACTUAL: BoundaryZone.COUNTERFACTUAL,
    OwnershipType.AMBIGUOUS: BoundaryZone.UNKNOWN,
    OwnershipType.UNKNOWN: BoundaryZone.UNKNOWN,
}


@dataclass
class OwnershipAttribution:
    """One ownership decision for a record (uncertainty preserved)."""

    ownership_type: str
    ref: str
    attribution_id: str = field(
        default_factory=lambda: f"OWN_{uuid.uuid4().hex[:8]}")
    confidence: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)

    @property
    def zone(self) -> str:
        return _OWNERSHIP_TO_ZONE.get(self.ownership_type, BoundaryZone.UNKNOWN)

    @property
    def is_self(self) -> bool:
        return self.ownership_type in (OwnershipType.SELF_INTERNAL,
                                       OwnershipType.SELF_RECEPTOR_STATE)

    @property
    def is_ambiguous(self) -> bool:
        return self.ownership_type in (OwnershipType.AMBIGUOUS,
                                       OwnershipType.UNKNOWN)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribution_id": self.attribution_id,
            "ownership_type": self.ownership_type,
            "ref": self.ref,
            "zone": self.zone,
            "confidence": round(self.confidence, 4),
            "is_self": self.is_self,
            "is_ambiguous": self.is_ambiguous,
            "evidence_refs": list(self.evidence_refs),
            "note": "ownership is operational; processed sensory input is not "
                    "'self', simulation is not real, annotation is not truth",
        }


@dataclass
class OwnershipAttributor:
    """Attributes ownership of records by their kind/provenance."""

    attributions: List[OwnershipAttribution] = field(default_factory=list)

    def attribute(self, kind: str, ref: str, *, confidence: float = 0.5,
                  evidence_refs: List[str] = None) -> OwnershipAttribution:
        """Attribute one record. ``kind`` is a coarse origin descriptor."""
        otype = self._classify(kind)
        att = OwnershipAttribution(ownership_type=otype, ref=ref,
                                   confidence=confidence,
                                   evidence_refs=list(evidence_refs or []))
        self.attributions.append(att)
        return att

    @staticmethod
    def _classify(kind: str) -> str:
        k = str(kind).lower()
        if "receptor" in k:
            return OwnershipType.SELF_RECEPTOR_STATE
        if "feeder" in k:
            return OwnershipType.EXTERNAL_FEEDER_ARTIFACT
        if "source" in k or "external" in k or "live" in k:
            return OwnershipType.EXTERNAL_SOURCE
        if "operator" in k or "annotation" in k:
            return OwnershipType.OPERATOR_ANNOTATION
        if "memory" in k or "replay" in k:
            return OwnershipType.MEMORY_REPLAY
        if "counterfactual" in k:
            return OwnershipType.COUNTERFACTUAL
        if "simulation" in k or "simulated" in k:
            return OwnershipType.INTERNAL_SIMULATION
        if "internal" in k or "metabolic" in k or "need" in k or "sign" in k \
                or "concept" in k or "prediction" in k:
            return OwnershipType.SELF_INTERNAL
        if "ambiguous" in k:
            return OwnershipType.AMBIGUOUS
        return OwnershipType.UNKNOWN

    def ambiguous(self) -> List[OwnershipAttribution]:
        return [a for a in self.attributions if a.is_ambiguous]

    def distribution(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for a in self.attributions:
            out[a.ownership_type] = out.get(a.ownership_type, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribution_count": len(self.attributions),
            "ambiguous_count": len(self.ambiguous()),
            "distribution": self.distribution(),
            "attributions": [a.to_dict() for a in self.attributions],
        }
