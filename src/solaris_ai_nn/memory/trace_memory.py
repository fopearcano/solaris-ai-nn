"""Trace memory -- a chronological record of what flowed through the loop.

No database, no ORM: just an in-memory list of lightweight records, optionally
mirrored to a JSONL file for long runs. This is the substrate's episodic trail:
events seen, actions taken, reactions received -- in order.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..runtime.persistence import JsonlWriter


@dataclass
class TraceRecord:
    """A single timestamped entry in the trace."""

    step: int
    category: str  # "event" | "action" | "reaction"
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


@dataclass
class TraceMemory:
    """Chronological event/action/reaction trace.

    Args:
        capacity: Max records kept in memory (oldest dropped beyond this).
        writer: Optional JSONL writer for durable, append-only persistence.
    """

    capacity: int = 10_000
    writer: Optional[JsonlWriter] = None
    records: List[TraceRecord] = field(default_factory=list)

    def _append(self, record: TraceRecord) -> None:
        self.records.append(record)
        if len(self.records) > self.capacity:
            # Drop oldest to bound memory during long-running experiments.
            self.records = self.records[-self.capacity :]
        if self.writer is not None:
            self.writer.write(
                {
                    "step": record.step,
                    "category": record.category,
                    "timestamp": record.timestamp,
                    **record.data,
                }
            )

    def record_event(self, step: int, kind: str, **data: Any) -> None:
        """Record an incoming/internal event."""
        self._append(TraceRecord(step=step, category="event", data={"kind": kind, **data}))

    def record_action(self, step: int, action: str, **data: Any) -> None:
        """Record an action the loop produced."""
        self._append(TraceRecord(step=step, category="action", data={"action": action, **data}))

    def record_reaction(self, step: int, valence: float, **data: Any) -> None:
        """Record a reaction/feedback received."""
        self._append(TraceRecord(step=step, category="reaction", data={"valence": valence, **data}))

    def __len__(self) -> int:
        return len(self.records)

    def recent(self, n: int) -> List[TraceRecord]:
        """Return the last ``n`` records."""
        return self.records[-n:]
