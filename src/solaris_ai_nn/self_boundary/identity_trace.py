"""Identity trace -- operational continuity metadata, NOT personal identity.

The :class:`IdentityTraceStore` writes append-only operational identity-trace
records (run identity, continuity anchors, active receptors, stable signs/concepts,
boundary shifts, memory gaps, restart events, drift events, safety blocks).
Identity here is operational continuity, NOT personal identity, and no
anthropomorphic identity language is used.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class IdentityTraceEventType:
    RUN_IDENTITY = "run_identity"
    CONTINUITY_ANCHOR = "continuity_anchor"
    BOUNDARY_SHIFT = "boundary_shift"
    MEMORY_GAP = "memory_gap"
    RESTART = "restart"
    MAJOR_DRIFT = "major_drift"
    SAFETY_BLOCK = "safety_block"

    ALL = (RUN_IDENTITY, CONTINUITY_ANCHOR, BOUNDARY_SHIFT, MEMORY_GAP,
           RESTART, MAJOR_DRIFT, SAFETY_BLOCK)


@dataclass
class IdentityTraceEvent:
    """One operational identity-trace event (continuity metadata, not personhood)."""

    event_type: str
    detail: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"IDT_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "event_type": self.event_type,
                "timestamp": self.timestamp, "detail": dict(self.detail),
                "note": "operational continuity metadata, not personal identity"}


@dataclass
class OperationalIdentityTrace:
    """The current operational identity snapshot (no anthropomorphic identity)."""

    run_id: str = field(default_factory=lambda: f"RUN_{uuid.uuid4().hex[:10]}")
    continuity_anchors: List[str] = field(default_factory=list)
    active_receptors: List[str] = field(default_factory=list)
    stable_signs: List[str] = field(default_factory=list)
    stable_proto_concepts: List[str] = field(default_factory=list)
    persistent_world_structures: List[str] = field(default_factory=list)
    boundary_shifts: int = 0
    memory_gaps: int = 0
    restart_events: int = 0
    major_drift_events: int = 0
    safety_blocks: int = 0
    limitations: List[str] = field(default_factory=lambda: [
        "operational continuity metadata, not personal identity",
        "no anthropomorphic identity is implied",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "continuity_anchors": list(self.continuity_anchors),
            "active_receptors": list(self.active_receptors),
            "stable_signs": list(self.stable_signs),
            "stable_proto_concepts": list(self.stable_proto_concepts),
            "persistent_world_structures": list(
                self.persistent_world_structures),
            "boundary_shifts": self.boundary_shifts,
            "memory_gaps": self.memory_gaps,
            "restart_events": self.restart_events,
            "major_drift_events": self.major_drift_events,
            "safety_blocks": self.safety_blocks,
            "limitations": list(self.limitations),
            "note": "identity trace is operational continuity, not personhood",
        }


@dataclass
class IdentityTraceStore:
    """Append-only persistence for identity-trace and boundary events."""

    state_dir: str = ".solaris_ai_nn_self_boundary"
    trace: OperationalIdentityTrace = field(
        default_factory=OperationalIdentityTrace)
    events: List[IdentityTraceEvent] = field(default_factory=list)
    persist: bool = True

    def _append(self, filename: str, record: Dict[str, Any]) -> None:
        if not self.persist:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        with open(os.path.join(self.state_dir, filename), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def record_event(self, event_type: str,
                     detail: Dict[str, Any]) -> IdentityTraceEvent:
        ev = IdentityTraceEvent(event_type=event_type, detail=dict(detail))
        self.events.append(ev)
        self._append("identity_trace.jsonl", ev.to_dict())
        if event_type == IdentityTraceEventType.RESTART:
            self.trace.restart_events += 1
        elif event_type == IdentityTraceEventType.MEMORY_GAP:
            self.trace.memory_gaps += 1
        elif event_type == IdentityTraceEventType.BOUNDARY_SHIFT:
            self.trace.boundary_shifts += 1
        elif event_type == IdentityTraceEventType.MAJOR_DRIFT:
            self.trace.major_drift_events += 1
        elif event_type == IdentityTraceEventType.SAFETY_BLOCK:
            self.trace.safety_blocks += 1
        return ev

    def record_boundary_event(self, payload: Dict[str, Any]) -> None:
        self._append("boundary_events.jsonl", payload)

    def record_continuity_break(self, payload: Dict[str, Any]) -> None:
        self._append("continuity_breaks.jsonl", payload)

    def event_count(self) -> int:
        return len(self.events)

    def snapshot(self) -> Dict[str, Any]:
        return {"trace": self.trace.to_dict(),
                "event_count": len(self.events)}
