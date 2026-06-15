"""Observation trace -- an auditable record of what the organism perceived.

:class:`ObservationTrace` collects :class:`TraceEvent`s during a demo run. Each
event preserves the tick, timestamp, modality, source, references, before/after
state (when available), provenance, and limitations -- so the demo's claims can
be checked against what actually happened.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TraceEventType:
    EXTERNAL_EVENT_SEEN = "external_event_seen"
    RECEPTOR_UPDATED = "receptor_updated"
    BASELINE_ESTIMATED = "baseline_estimated"
    BASELINE_SHIFT_DETECTED = "baseline_shift_detected"
    FIELD_PRESSURE_CHANGED = "field_pressure_changed"
    ABSENCE_DETECTED = "absence_detected"
    RHYTHM_DETECTED = "rhythm_detected"
    INVARIANT_CANDIDATE_CREATED = "invariant_candidate_created"
    CROSS_MODAL_RELATION_CREATED = "cross_modal_relation_created"
    ATTENTION_SHIFTED = "attention_shifted"
    PROTO_SYMBOL_CANDIDATE_CREATED = "proto_symbol_candidate_created"
    WORLD_MODEL_NODE_CREATED = "world_model_node_created"
    HYPOTHESIS_SEEDED = "hypothesis_seeded"
    LOGOS_TENSION_CREATED = "logos_tension_created"
    CHANGED_PERCEPTION_PROBE_RESULT = "changed_perception_probe_result"
    SAFETY_BLOCK = "safety_block"

    ALL = (EXTERNAL_EVENT_SEEN, RECEPTOR_UPDATED, BASELINE_ESTIMATED,
           BASELINE_SHIFT_DETECTED, FIELD_PRESSURE_CHANGED, ABSENCE_DETECTED,
           RHYTHM_DETECTED, INVARIANT_CANDIDATE_CREATED,
           CROSS_MODAL_RELATION_CREATED, ATTENTION_SHIFTED,
           PROTO_SYMBOL_CANDIDATE_CREATED, WORLD_MODEL_NODE_CREATED,
           HYPOTHESIS_SEEDED, LOGOS_TENSION_CREATED,
           CHANGED_PERCEPTION_PROBE_RESULT, SAFETY_BLOCK)


@dataclass
class TraceEvent:
    event_type: str
    tick: int = 0
    modality: Optional[str] = None
    source_id: Optional[str] = None
    event_refs: List[str] = field(default_factory=list)
    before: Optional[Any] = None
    after: Optional[Any] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ObservationTrace:
    events: List[TraceEvent] = field(default_factory=list)
    max_events: int = 5000

    def record(self, event_type: str, *, tick: int = 0,
               modality: Optional[str] = None, source_id: Optional[str] = None,
               event_refs: Optional[List[str]] = None, before: Any = None,
               after: Any = None, provenance: Optional[Dict[str, Any]] = None,
               limitations: Optional[List[str]] = None,
               detail: str = "") -> Optional[TraceEvent]:
        if event_type not in TraceEventType.ALL:
            raise ValueError(f"unknown trace event {event_type!r}")
        if len(self.events) >= self.max_events:
            return None
        event = TraceEvent(
            event_type=event_type, tick=tick, modality=modality,
            source_id=source_id, event_refs=list(event_refs or []),
            before=before, after=after, provenance=dict(provenance or {}),
            limitations=list(limitations or []), detail=detail)
        self.events.append(event)
        return event

    def of_type(self, event_type: str) -> List[TraceEvent]:
        return [e for e in self.events if e.event_type == event_type]

    def count(self, event_type: str) -> int:
        return len(self.of_type(event_type))

    def counts_by_type(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.events:
            out[e.event_type] = out.get(e.event_type, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_count": len(self.events),
            "counts_by_type": self.counts_by_type(),
            "events": [e.to_dict() for e in self.events[:1000]],
        }
