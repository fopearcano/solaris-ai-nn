"""Autobiographical memory -- the developmental history as grounded rows.

Templated, evidence-backed events ("Runtime survived 24h equivalent",
"Restart gap detected and identity continuity restored") persisted as
JSONL. No first-person claims, no consciousness claims, and every event
says whether it happened in real wall-clock time or a simulated-time
test -- lived history and accelerated tests are never confused.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_FORBIDDEN_FRAGMENTS = ("i am", "i want", "i feel", "i survived",
                        "my life", "i remember", "i grew")

CATEGORIES = ("survival", "habit", "prediction", "mysterium",
              "world_model", "identity", "boundary", "consolidation",
              "pruning", "epoch", "phase", "runtime")


@dataclass
class AutobiographicalEvent:
    """One grounded row of developmental history."""

    text: str
    category: str = "runtime"
    evidence_refs: List[str] = field(default_factory=list)
    lifetime_s: float = 0.0
    simulated: bool = True
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.evidence_refs:
            raise ValueError("every autobiographical event must include "
                             "evidence references")
        lowered = f" {self.text.lower()} "
        for fragment in _FORBIDDEN_FRAGMENTS:
            if f" {fragment} " in lowered \
                    or lowered.strip().startswith(fragment):
                raise ValueError(
                    f"autobiographical text contains first-person "
                    f"fragment {fragment!r}; the history is written in "
                    "system-observational voice")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AutobiographicalMemory:
    """Bounded in memory, append-only JSONL on disk."""

    state_dir: Optional[Union[str, Path]] = None
    max_events: int = 1000
    events: List[AutobiographicalEvent] = field(default_factory=list,
                                                init=False)
    rows_written: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.path = (Path(self.state_dir)
                     / "autobiographical_memory.jsonl"
                     if self.state_dir else None)

    def add(self, text: str, evidence: List[str],
            category: str = "runtime", lifetime_s: float = 0.0,
            simulated: bool = True) -> AutobiographicalEvent:
        event = AutobiographicalEvent(
            text=str(text), category=category,
            evidence_refs=list(evidence), lifetime_s=lifetime_s,
            simulated=simulated)
        self.events.append(event)
        self.events = self.events[-self.max_events:]
        self._write(event)
        return event

    def record_milestone(self, milestone: Any) -> AutobiographicalEvent:
        return self.add(
            text=milestone.description,
            evidence=list(milestone.evidence_refs),
            category="phase" if "phase" in milestone.type
            else "survival" if "survival" in milestone.type
            else "runtime",
            lifetime_s=milestone.lifetime_s,
            simulated=milestone.simulated)

    def _write(self, event: AutobiographicalEvent) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")
        self.rows_written += 1

    # -- views --------------------------------------------------------------------

    def tail(self, limit: int = 10) -> List[AutobiographicalEvent]:
        return self.events[-limit:]

    def as_story(self, limit: int = 20) -> str:
        return "\n".join(e.text for e in self.events[-limit:])

    def snapshot(self) -> Dict[str, Any]:
        simulated = sum(1 for e in self.events if e.simulated)
        return {
            "events_in_memory": len(self.events),
            "rows_written": self.rows_written,
            "path": str(self.path) if self.path else None,
            "simulated_events": simulated,
            "real_time_events": len(self.events) - simulated,
            "recent": [e.to_dict() for e in self.events[-5:]],
            "note": "grounded developmental history in observational "
                    "voice; no first-person or consciousness claims",
        }
