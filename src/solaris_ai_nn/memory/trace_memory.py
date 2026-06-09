"""Trace memory -- a chronological record of what flowed through the loop.

No database, no ORM: just an in-memory list of lightweight records, optionally
mirrored to a JSONL file for long runs. This is the substrate's episodic trail:
events seen, actions taken, reactions received -- in order.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:  # Avoid importing runtime at load time (breaks an import cycle).
    from ..runtime.persistence import JsonlWriter


@dataclass
class TraceRecord:
    """A single timestamped entry in the trace."""

    step: int
    category: str  # "event" | "action" | "reaction" | "signal"
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_row(self) -> Dict[str, Any]:
        return {"step": self.step, "category": self.category, "timestamp": self.timestamp, **self.data}


@dataclass
class TraceMemory:
    """Chronological event/action/reaction trace.

    Args:
        capacity: Max records kept in memory (oldest dropped beyond this).
        writer: Optional JSONL writer for durable, append-only persistence.
        path: Optional path; when given (and no explicit ``writer``), an
            append-mode JSONL writer is opened so the trace survives restarts and
            can be replayed. Append mode means the trace is never silently
            truncated.
    """

    capacity: int = 10_000
    writer: Optional["JsonlWriter"] = None
    path: Optional[Union[str, Path]] = None
    records: List[TraceRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.writer is None and self.path is not None:
            from ..runtime.persistence import JsonlWriter  # local import: avoid cycle

            self.writer = JsonlWriter(self.path, append=True)

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

    def record_signal(
        self,
        step: int,
        signal_dict: Dict[str, Any],
        lifetime_step: int = 0,
        reaction: Optional[float] = None,
    ) -> None:
        """Record a full, replayable input signal (plus any reaction valence).

        Unlike :meth:`record_event` (which keeps a lossy summary), this stores the
        complete serialised signal so :mod:`solaris_ai_nn.runtime.replay` can feed
        it back into a bridge verbatim.
        """
        self._append(
            TraceRecord(
                step=step,
                category="signal",
                data={"lifetime_step": lifetime_step, "signal": signal_dict, "reaction": reaction},
            )
        )

    # -- persistence / inspection ------------------------------------------

    def append_event(self, **fields: Any) -> None:
        """Append an arbitrary row to the trace (category defaults to ``event``)."""
        category = fields.pop("category", "event")
        step = fields.pop("step", len(self.records))
        self._append(TraceRecord(step=step, category=category, data=fields))

    @staticmethod
    def load(path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load a trace JSONL file into a list of row dicts (empty if absent)."""
        from ..runtime.persistence import read_jsonl  # local import: avoid cycle

        if not Path(path).exists():
            return []
        return list(read_jsonl(path))

    def tail(self, n: int) -> List[Dict[str, Any]]:
        """Return the last ``n`` in-memory records as row dicts."""
        return [r.to_row() for r in self.records[-n:]]

    def count(self) -> int:
        """Number of in-memory records."""
        return len(self.records)

    def clear(self, confirm: bool = False) -> None:
        """Clear the in-memory trace. Requires ``confirm=True`` (never silent).

        The on-disk JSONL is append-only and is deliberately NOT deleted here --
        trace memory is never silently destroyed.
        """
        if not confirm:
            raise ValueError("clear() requires confirm=True; trace memory is not silently deleted")
        self.records = []

    def __len__(self) -> int:
        return len(self.records)

    def recent(self, n: int) -> List[TraceRecord]:
        """Return the last ``n`` records."""
        return self.records[-n:]
