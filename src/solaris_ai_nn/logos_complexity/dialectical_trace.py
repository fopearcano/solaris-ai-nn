"""Dialectical trace -- an append-only record of LOGOS dynamics over time.

So later analysis can ask whether LOGOS dynamics produce *structural change*,
every notable LOGOS event (tension detected, fracture recorded, synthesis
proposed/applied/refused, tension preserved, hypothesis spawned, replay/
sampling/repair requested, complexity shift, Esc triggered) becomes a
:class:`DialecticalTraceEvent` written to ``dialectical_trace.jsonl``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class TraceEventType:
    TENSION_DETECTED = "tension_detected"
    FRACTURE_RECORDED = "fracture_recorded"
    SYNTHESIS_PROPOSED = "synthesis_proposed"
    SYNTHESIS_APPLIED = "synthesis_applied"
    SYNTHESIS_REFUSED = "synthesis_refused"
    TENSION_PRESERVED = "tension_preserved"
    HYPOTHESIS_SPAWNED = "hypothesis_spawned"
    REPLAY_REQUESTED = "replay_requested"
    SAMPLING_REQUESTED = "sampling_requested"
    REPAIR_REQUESTED = "repair_requested"
    COMPLEXITY_SHIFT = "complexity_shift"
    ESC_TRIGGERED = "esc_triggered"

    ALL = (TENSION_DETECTED, FRACTURE_RECORDED, SYNTHESIS_PROPOSED,
           SYNTHESIS_APPLIED, SYNTHESIS_REFUSED, TENSION_PRESERVED,
           HYPOTHESIS_SPAWNED, REPLAY_REQUESTED, SAMPLING_REQUESTED,
           REPAIR_REQUESTED, COMPLEXITY_SHIFT, ESC_TRIGGERED)


@dataclass
class DialecticalTraceEvent:
    """One recorded LOGOS dynamic."""

    event_type: str
    tension_id: str = ""
    detail: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event_type not in TraceEventType.ALL:
            raise ValueError(f"unknown trace event type {self.event_type!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DialecticalTrace:
    """Append-only JSONL trace of LOGOS dynamics."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    events: List[DialecticalTraceEvent] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.log_path = (Path(self.state_dir) / "dialectical_trace.jsonl"
                         if self.state_dir else None)

    def record(self, event_type: str, tension_id: str = "", detail: str = "",
               **metadata: Any) -> DialecticalTraceEvent:
        event = DialecticalTraceEvent(event_type=event_type,
                                      tension_id=tension_id, detail=detail,
                                      metadata=dict(metadata))
        self.events.append(event)
        self.events = self.events[-5000:]
        self.counts[event_type] = self.counts.get(event_type, 0) + 1
        if self.write_log and self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict(), default=str) + "\n")
        return event

    def snapshot(self) -> Dict[str, Any]:
        return {
            "event_count": len(self.events),
            "counts": dict(self.counts),
            "log_path": str(self.log_path) if self.log_path else None,
            "recent": [e.to_dict() for e in self.events[-5:]],
        }
