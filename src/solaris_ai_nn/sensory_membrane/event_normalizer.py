"""Sensory event normalizer -- raw reads become canonical, provenanced stimuli.

A :class:`RawSensoryEvent` (what an adapter produced) is turned into a
:class:`NormalizedSensoryEvent` with novelty/intensity heuristics, a recurrence
key, and an absence marker, and then into canonical Solaris-AI-NN dicts
(Stimulus-like, optionally MeaningEvent-like, and -- only when the source
supplies an *external* valence hint -- a Reaction-like dict clearly marked as a
hint, never a system outcome). Input text is never command semantics.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .modality import SensoryModality
from .provenance import hash_text


@dataclass
class RawSensoryEvent:
    """What an adapter emits before normalization."""

    source_id: str
    source_type: str
    modality: str = SensoryModality.UNKNOWN
    payload: Any = None
    raw_line: Optional[str] = None
    numeric_values: Dict[str, float] = field(default_factory=dict)
    is_absence: bool = False
    malformed: bool = False
    external_valence_hint: Optional[float] = None
    adapter_name: str = ""
    is_simulated: bool = False
    trust_level: str = "low"
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_hash(self) -> str:
        basis = f"{self.source_id}|{self.modality}|{self.raw_line}|" \
                f"{self.payload}|{sorted(self.numeric_values.items())}"
        return hash_text(basis)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "event_hash": self.event_hash}


@dataclass
class NormalizedSensoryEvent:
    """A canonicalized sensory event with heuristics and provenance refs."""

    event_id: str
    source_id: str
    source_type: str
    modality: str
    payload_summary: str = ""
    numeric_values: Dict[str, float] = field(default_factory=dict)
    novelty: float = 0.0
    intensity: float = 0.0
    recurrence_key: str = ""
    is_absence: bool = False
    external_valence_hint: Optional[float] = None
    provenance_refs: List[str] = field(default_factory=list)
    safety_tags: List[str] = field(default_factory=list)
    is_simulated: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    # -- canonical conversions --------------------------------------------------

    def to_stimulus_dict(self) -> Dict[str, Any]:
        """A Stimulus-like dict (read-only environmental input)."""
        return {
            "kind": "Stimulus",
            "modality": self.modality,
            "payload": self.payload_summary,
            "intensity": round(self.intensity, 4),
            "is_absence": self.is_absence,
            "origin": "read_only_environmental_input",
            "source_id": self.source_id,
            "provenance_refs": list(self.provenance_refs),
            "executable_scope": "none",
        }

    def to_meaning_dict(self) -> Optional[Dict[str, Any]]:
        """A MeaningEvent-like dict when the event carries novelty/recurrence."""
        if self.novelty <= 0.0 and not self.recurrence_key:
            return None
        return {
            "kind": "MeaningEvent",
            "meaning": f"environmental:{self.recurrence_key or self.modality}",
            "novelty": round(self.novelty, 4),
            "origin": "read_only_environmental_input",
            "source_id": self.source_id,
            "note": "environmental association, not human understanding",
        }

    def to_reaction_hint_dict(self) -> Optional[Dict[str, Any]]:
        """A Reaction-like dict ONLY if the source gave an external valence hint.

        It is explicitly marked an external hint, never a system outcome.
        """
        if self.external_valence_hint is None:
            return None
        return {
            "kind": "ReactionHint",
            "valence": float(self.external_valence_hint),
            "origin": "external_environment_hint",
            "is_system_outcome": False,
            "source_id": self.source_id,
        }


@dataclass
class SensoryEventNormalizer:
    """Normalizes raw sensory events; tracks recurrence for novelty scoring."""

    _seen: Dict[str, int] = field(default_factory=dict, init=False)

    def normalize(self, raw: RawSensoryEvent,
                  provenance_refs: Optional[List[str]] = None,
                  ) -> NormalizedSensoryEvent:
        recurrence_key = self._recurrence_key(raw)
        seen = self._seen.get(recurrence_key, 0)
        self._seen[recurrence_key] = seen + 1
        # Novelty: high when unseen, decaying with recurrence (bounded).
        novelty = 0.0 if raw.malformed else round(1.0 / (1.0 + seen), 4)
        intensity = self._intensity(raw, novelty)
        safety_tags = ["read_only_environmental_input"]
        if raw.is_simulated:
            safety_tags.append("simulated_source")
        if raw.malformed:
            safety_tags.append("malformed")
        # A hard, explicit tag: this is never an operator command.
        safety_tags.append("not_operator_command")
        return NormalizedSensoryEvent(
            event_id=f"SEV_{uuid.uuid4().hex[:10]}",
            source_id=raw.source_id, source_type=raw.source_type,
            modality=raw.modality,
            payload_summary=self._summary(raw),
            numeric_values=dict(raw.numeric_values),
            novelty=novelty, intensity=intensity,
            recurrence_key=recurrence_key, is_absence=raw.is_absence,
            external_valence_hint=raw.external_valence_hint,
            provenance_refs=list(provenance_refs or [raw.event_hash]),
            safety_tags=safety_tags, is_simulated=raw.is_simulated,
            timestamp=raw.timestamp)

    def absence_event(self, source_id: str, source_type: str,
                      modality: str = SensoryModality.TEMPORAL,
                      ) -> NormalizedSensoryEvent:
        """A canonical absence stimulus (missing expected input)."""
        return NormalizedSensoryEvent(
            event_id=f"SEV_{uuid.uuid4().hex[:10]}", source_id=source_id,
            source_type=source_type, modality=modality,
            payload_summary="absence: expected input missing",
            novelty=0.5, intensity=0.4, recurrence_key=f"absence:{source_id}",
            is_absence=True,
            provenance_refs=[hash_text(f"absence:{source_id}")],
            safety_tags=["read_only_environmental_input", "absence",
                         "not_operator_command"])

    def _recurrence_key(self, raw: RawSensoryEvent) -> str:
        if raw.modality == SensoryModality.NUMERIC and raw.numeric_values:
            trend = raw.metadata.get("trend", "")
            return f"{raw.source_id}:numeric:{trend}"
        if raw.modality in (SensoryModality.FILE_PRESENCE,
                            SensoryModality.FILE_CHANGE):
            return f"{raw.source_id}:{raw.modality}"
        text = str(raw.payload or raw.raw_line or "")[:64]
        return f"{raw.source_id}:{raw.modality}:{text.strip().lower()}"

    @staticmethod
    def _intensity(raw: RawSensoryEvent, novelty: float) -> float:
        if raw.is_absence:
            return 0.4
        if raw.modality == SensoryModality.NUMERIC and raw.numeric_values:
            if raw.metadata.get("trend") == "spike":
                return 0.9
            if raw.metadata.get("trend") in ("rising", "falling"):
                return 0.6
            return 0.3
        return round(min(1.0, 0.3 + 0.6 * novelty), 4)

    @staticmethod
    def _summary(raw: RawSensoryEvent) -> str:
        if raw.is_absence:
            return "absence"
        if raw.numeric_values:
            trend = raw.metadata.get("trend", "")
            return f"numeric[{trend}]: " + ", ".join(
                f"{k}={v}" for k, v in list(raw.numeric_values.items())[:4])
        text = str(raw.payload or raw.raw_line or "")
        return text[:160]
