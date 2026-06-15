"""Cross-modal perception -- the relations *between* peculiar senses.

A :class:`CrossModalDetector` watches the recent timeline of events across
modalities and records :class:`CrossModalRelation`s: an RF burst followed by a
vibration, a thermal drift before a machine rhythm, a silence shared across
modalities. Cross-modal structure is stored without forcing a human object
ontology, and it is one of the main sources of emergent intelligence-like
patterns.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class CrossModalRelationType:
    FOLLOWED_BY = "followed_by"
    PRECEDED_BY = "preceded_by"
    COINCIDES_WITH = "coincides_with"
    SHARED_SILENCE = "shared_silence"
    INTERFERENCE_DURING_STABILITY = "interference_during_stability"
    ABSENCE_AFTER_RECURRENCE = "absence_after_recurrence"

    ALL = (FOLLOWED_BY, PRECEDED_BY, COINCIDES_WITH, SHARED_SILENCE,
           INTERFERENCE_DURING_STABILITY, ABSENCE_AFTER_RECURRENCE)


@dataclass
class CrossModalEvent:
    """A single observed (modality, source, timestamp, intensity) point."""

    modality: str
    source_id: str
    timestamp: float
    intensity: float

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class CrossModalRelation:
    """A detected relation between two modalities (no human ontology)."""

    relation_type: str
    modality_a: str
    modality_b: str
    source_a: str
    source_b: str
    lag: float
    support: int = 1
    provenance: Dict[str, Any] = field(default_factory=dict)
    relation_id: str = field(default_factory=lambda: f"XMR_{uuid.uuid4().hex[:8]}")

    @property
    def key(self) -> Tuple[str, str, str]:
        return (self.relation_type, self.modality_a, self.modality_b)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "modality_a": self.modality_a,
            "modality_b": self.modality_b,
            "source_a": self.source_a,
            "source_b": self.source_b,
            "lag": self.lag,
            "support": self.support,
            "provenance": dict(self.provenance),
        }


@dataclass
class CrossModalDetector:
    """Detects temporal relations between events of different modalities."""

    coincidence_window: float = 0.5
    sequence_window: float = 5.0
    _recent: List[CrossModalEvent] = field(default_factory=list)
    relations: Dict[Tuple[str, str, str], CrossModalRelation] = field(
        default_factory=dict)

    def observe(self, modality: str, source_id: str, timestamp: float,
                intensity: float) -> List[CrossModalRelation]:
        event = CrossModalEvent(modality=modality, source_id=source_id,
                                timestamp=timestamp, intensity=intensity)
        out: List[CrossModalRelation] = []
        for prior in self._recent[-25:]:
            if prior.modality == modality:
                continue
            lag = timestamp - prior.timestamp
            if lag < 0:
                continue
            if lag <= self.coincidence_window:
                out.append(self._record(
                    CrossModalRelationType.COINCIDES_WITH, prior, event, lag))
            elif lag <= self.sequence_window:
                out.append(self._record(
                    CrossModalRelationType.FOLLOWED_BY, prior, event, lag))
        self._recent.append(event)
        self._recent = self._recent[-50:]
        return out

    def _record(self, relation_type: str, prior: CrossModalEvent,
                event: CrossModalEvent, lag: float) -> CrossModalRelation:
        key = (relation_type, prior.modality, event.modality)
        existing = self.relations.get(key)
        if existing is not None:
            existing.support += 1
            existing.lag = 0.7 * existing.lag + 0.3 * lag
            return existing
        rel = CrossModalRelation(
            relation_type=relation_type, modality_a=prior.modality,
            modality_b=event.modality, source_a=prior.source_id,
            source_b=event.source_id, lag=lag,
            provenance={"source_a": prior.source_id,
                        "source_b": event.source_id})
        self.relations[key] = rel
        return rel

    def record_shared_silence(self, modalities: List[str]) -> Optional[
            CrossModalRelation]:
        if len(modalities) < 2:
            return None
        key = (CrossModalRelationType.SHARED_SILENCE,
               modalities[0], modalities[1])
        rel = self.relations.get(key)
        if rel is None:
            rel = CrossModalRelation(
                relation_type=CrossModalRelationType.SHARED_SILENCE,
                modality_a=modalities[0], modality_b=modalities[1],
                source_a="*", source_b="*", lag=0.0,
                provenance={"modalities": list(modalities)})
            self.relations[key] = rel
        else:
            rel.support += 1
        return rel

    def relation_count(self) -> int:
        return len(self.relations)

    def cross_modal_pressure(self) -> float:
        return min(1.0, len(self.relations) / 4.0) if self.relations else 0.0

    def all_relations(self) -> List[CrossModalRelation]:
        return list(self.relations.values())

    def snapshot(self) -> Dict[str, Any]:
        return {"cross_modal_relation_count": len(self.relations),
                "relations": [r.to_dict() for r in self.relations.values()]}
