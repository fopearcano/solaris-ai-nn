"""Sensory buffer -- ordered, deduplicated, rate-limited event holding.

The :class:`SensoryBuffer` holds recent normalized events, deduplicates by
recurrence key within a window, rate-limits per poll, preserves order, and
emits batches (e.g. to the ConscienceBus). It tracks dropped and delayed
events and persists the buffer and the full event stream to JSONL.
"""

from __future__ import annotations

import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional


@dataclass
class BufferedSensoryEvent:
    """A normalized event held in the buffer with admission metadata."""

    event: Dict[str, Any]
    admitted_at: float = field(default_factory=time.time)
    delayed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"admitted_at": self.admitted_at, "delayed": self.delayed,
                "event": self.event}


@dataclass
class SensoryBuffer:
    """Bounded, deduplicating, rate-limited buffer of normalized events."""

    state_dir: Optional[str] = None
    capacity: int = 1000
    max_per_batch: int = 200
    dedup_window: int = 256
    write_log: bool = True
    _buffer: Deque[BufferedSensoryEvent] = field(default_factory=deque,
                                                init=False)
    _recent_keys: Deque[str] = field(default_factory=deque, init=False)
    dropped_count: int = field(default=0, init=False)
    delayed_count: int = field(default=0, init=False)
    admitted_count: int = field(default=0, init=False)
    duplicate_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.buffer_path = (os.path.join(self.state_dir, "sensory_buffer.jsonl")
                            if self.state_dir else None)
        self.events_path = (os.path.join(self.state_dir, "sensory_events.jsonl")
                            if self.state_dir else None)

    def admit(self, normalized: Any) -> bool:
        """Admit one normalized event (dict or object). Returns admitted?"""
        event = (normalized.to_dict() if hasattr(normalized, "to_dict")
                 else dict(normalized))
        key = event.get("recurrence_key") or event.get("event_id", "")
        if key and key in self._recent_keys:
            self.duplicate_count += 1
            return False
        if len(self._buffer) >= self.capacity:
            self._buffer.popleft()
            self.dropped_count += 1
        buffered = BufferedSensoryEvent(event=event)
        self._buffer.append(buffered)
        self.admitted_count += 1
        if key:
            self._recent_keys.append(key)
            while len(self._recent_keys) > self.dedup_window:
                self._recent_keys.popleft()
        self._append(self.events_path, event)
        self._append(self.buffer_path, buffered.to_dict())
        return True

    def admit_many(self, events: List[Any]) -> int:
        return sum(1 for e in events if self.admit(e))

    def emit_batch(self) -> List[Dict[str, Any]]:
        """Pop up to ``max_per_batch`` events in order for publication."""
        batch: List[Dict[str, Any]] = []
        while self._buffer and len(batch) < self.max_per_batch:
            batch.append(self._buffer.popleft().event)
        return batch

    def pending(self) -> int:
        return len(self._buffer)

    def _append(self, path: Optional[str], obj: Dict[str, Any]) -> None:
        if not (self.write_log and path):
            return
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, default=str) + "\n")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pending": self.pending(),
            "admitted_count": self.admitted_count,
            "dropped_count": self.dropped_count,
            "delayed_count": self.delayed_count,
            "duplicate_count": self.duplicate_count,
            "capacity": self.capacity,
            "buffer_path": self.buffer_path,
            "events_path": self.events_path,
        }
