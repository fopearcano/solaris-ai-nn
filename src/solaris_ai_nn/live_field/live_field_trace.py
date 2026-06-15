"""Live field trace -- an auditable record of a live read-only pilot.

:class:`LiveFieldTrace` records what happened during a live-field run: which
feeders were seen or missing, how source health changed, which envelopes were
ingested or rejected, and what the sensorium detected. Each event preserves the
tick, source/feeder identity, modality, references, source health, before/after
state, provenance, and limitations.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LiveFieldTraceEventType:
    FEEDER_SEEN = "feeder_seen"
    FEEDER_MISSING = "feeder_missing"
    SOURCE_HEALTH_CHANGED = "source_health_changed"
    EXTERNAL_EVENT_INGESTED = "external_event_ingested"
    ENVELOPE_INVALID = "envelope_invalid"
    RECEPTOR_UPDATED = "receptor_updated"
    SENSORY_FIELD_UPDATED = "sensory_field_updated"
    SOURCE_ABSENCE_DETECTED = "source_absence_detected"
    RHYTHM_DETECTED = "rhythm_detected"
    INVARIANT_CANDIDATE_CREATED = "invariant_candidate_created"
    CROSS_MODAL_RELATION_CREATED = "cross_modal_relation_created"
    ATTENTION_SHIFTED = "attention_shifted"
    CHANGED_PERCEPTION_PROBE_RESULT = "changed_perception_probe_result"
    COMPARISON_RESULT = "comparison_result"
    SAFETY_BLOCK = "safety_block"

    ALL = (FEEDER_SEEN, FEEDER_MISSING, SOURCE_HEALTH_CHANGED,
           EXTERNAL_EVENT_INGESTED, ENVELOPE_INVALID, RECEPTOR_UPDATED,
           SENSORY_FIELD_UPDATED, SOURCE_ABSENCE_DETECTED, RHYTHM_DETECTED,
           INVARIANT_CANDIDATE_CREATED, CROSS_MODAL_RELATION_CREATED,
           ATTENTION_SHIFTED, CHANGED_PERCEPTION_PROBE_RESULT,
           COMPARISON_RESULT, SAFETY_BLOCK)


@dataclass
class LiveFieldTraceEvent:
    event_type: str
    tick: int = 0
    source_id: Optional[str] = None
    feeder_id: Optional[str] = None
    modality: Optional[str] = None
    event_refs: List[str] = field(default_factory=list)
    source_health: Optional[str] = None
    before: Optional[Any] = None
    after: Optional[Any] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LiveFieldTrace:
    events: List[LiveFieldTraceEvent] = field(default_factory=list)
    max_events: int = 5000

    def record(self, event_type: str, **kw: Any) -> Optional[LiveFieldTraceEvent]:
        if event_type not in LiveFieldTraceEventType.ALL:
            raise ValueError(f"unknown live trace event {event_type!r}")
        if len(self.events) >= self.max_events:
            return None
        event = LiveFieldTraceEvent(event_type=event_type, **kw)
        self.events.append(event)
        return event

    def of_type(self, event_type: str) -> List[LiveFieldTraceEvent]:
        return [e for e in self.events if e.event_type == event_type]

    def count(self, event_type: str) -> int:
        return len(self.of_type(event_type))

    def counts_by_type(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.events:
            out[e.event_type] = out.get(e.event_type, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {"event_count": len(self.events),
                "counts_by_type": self.counts_by_type(),
                "events": [e.to_dict() for e in self.events[:1000]]}
