"""Body schema -- the receptor/sensory-membrane "body", not a biological body.

The :class:`SensoriumBodySchema` is the set of internal receptors and sensory
membranes Solaris treats as body-like organs. External feeders are NOT body parts;
they are external nerve-like signal sources. This is not a physical body unless an
embodiment module provides one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .boundary_state import BoundaryConfidence


@dataclass
class ReceptorBodyPart:
    """One receptor treated as a body-like sensory organ (not a feeder)."""

    receptor_id: str
    modality: str = ""
    source_link: str = ""
    reliability: float = 1.0
    fatigue: float = 0.0
    saturation: float = 0.0
    sensitivity: float = 0.0
    silence_duration: float = 0.0
    boundary_confidence: float = 1.0
    last_update: float = 0.0
    related_receptors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def confidence_band(self) -> str:
        return BoundaryConfidence.band(self.boundary_confidence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receptor_id": self.receptor_id,
            "modality": self.modality,
            "source_link": self.source_link,
            "reliability": round(self.reliability, 4),
            "fatigue": round(self.fatigue, 4),
            "saturation": round(self.saturation, 4),
            "sensitivity": round(self.sensitivity, 4),
            "silence_duration": round(self.silence_duration, 4),
            "boundary_confidence": round(self.boundary_confidence, 4),
            "confidence_band": self.confidence_band,
            "last_update": self.last_update,
            "related_receptors": list(self.related_receptors),
            "metadata": dict(self.metadata),
            "note": "receptor body-organ; external feeders are NOT body parts",
        }


@dataclass
class BodySchemaUpdate:
    receptor_id: str
    change: str
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoriumBodySchema:
    """The receptor/membrane body (organs), distinct from external feeders."""

    parts: Dict[str, ReceptorBodyPart] = field(default_factory=dict)
    updates: List[BodySchemaUpdate] = field(default_factory=list)

    def update_from_receptor(self, receptor: Any) -> ReceptorBodyPart:
        """Build/refresh a body part from a plural-sensorium receptor."""
        rid = getattr(receptor, "receptor_id", "")
        sens = getattr(receptor, "sensitivity", None)
        sensitivity = (getattr(sens, "value", 0.0)
                       if sens is not None and not isinstance(sens, (int, float))
                       else float(sens) if isinstance(sens, (int, float))
                       else 0.0)
        # Boundary confidence falls with low reliability (corruption risk).
        reliability = float(getattr(receptor, "reliability", 1.0))
        part = ReceptorBodyPart(
            receptor_id=rid,
            modality=getattr(receptor, "modality", ""),
            source_link=getattr(receptor, "source_id", ""),
            reliability=reliability,
            fatigue=float(getattr(receptor, "fatigue", 0.0)),
            saturation=float(getattr(receptor, "saturation", 0.0)),
            sensitivity=sensitivity,
            silence_duration=float(getattr(receptor, "silence_duration", 0.0)),
            boundary_confidence=round(0.5 + 0.5 * reliability, 4),
            last_update=float(getattr(receptor, "last_event_time", 0.0) or 0.0),
            metadata={"adaptation_state":
                      getattr(receptor, "adaptation_state", "")})
        if rid in self.parts:
            self.updates.append(BodySchemaUpdate(
                receptor_id=rid, change="refresh",
                detail={"reliability": reliability}))
        else:
            self.updates.append(BodySchemaUpdate(
                receptor_id=rid, change="add"))
        self.parts[rid] = part
        return part

    def link_related(self) -> None:
        """Relate receptors that share a modality (body-organ relations)."""
        by_modality: Dict[str, List[str]] = {}
        for p in self.parts.values():
            by_modality.setdefault(p.modality, []).append(p.receptor_id)
        for p in self.parts.values():
            p.related_receptors = [r for r in by_modality.get(p.modality, [])
                                   if r != p.receptor_id]

    @property
    def part_count(self) -> int:
        return len(self.parts)

    def stability(self) -> float:
        if not self.parts:
            return 0.0
        return round(sum(p.boundary_confidence for p in self.parts.values())
                     / len(self.parts), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receptor_body_part_count": self.part_count,
            "body_schema_stability": self.stability(),
            "parts": [p.to_dict() for p in self.parts.values()],
            "update_count": len(self.updates),
            "note": "the body is the receptor/sensory-membrane structure, not a "
                    "biological body; feeders are external nerve-like signals",
        }
