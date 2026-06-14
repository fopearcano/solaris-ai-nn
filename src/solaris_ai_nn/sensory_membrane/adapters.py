"""Sensory adapter contract -- read-only, payload-never-executed, provenanced.

A :class:`SensoryAdapter` polls one source and returns raw sensory events. The
base class fixes the contract: adapters read only, never execute source
payloads, tolerate malformed rows/events, and emit provenance. Concrete
adapters (JSONL/text/numeric/folder) subclass and implement ``_poll``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .event_normalizer import RawSensoryEvent
from .sources import SensorySourceConfig


class AdapterError(Exception):
    """A non-fatal adapter error (read failures degrade, never crash)."""


@dataclass
class AdapterResult:
    """The outcome of one poll: events plus health counters."""

    events: List[RawSensoryEvent] = field(default_factory=list)
    malformed: int = 0
    read_errors: int = 0
    rotated: bool = False
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"event_count": len(self.events), "malformed": self.malformed,
                "read_errors": self.read_errors, "rotated": self.rotated,
                "note": self.note}


class SensoryAdapter:
    """Base read-only adapter. Subclasses implement ``_poll``."""

    name = "sensory_adapter"

    def __init__(self, config: SensorySourceConfig) -> None:
        self.config = config
        self._closed = False

    # -- contract ---------------------------------------------------------------

    def poll(self) -> AdapterResult:
        """Read-only poll; never raises past this boundary."""
        if self._closed:
            return AdapterResult(note="adapter closed")
        if self.config.path and self.config.is_real_read_only \
                and not os.path.exists(self.config.path):
            return AdapterResult(read_errors=1, note="source missing")
        try:
            return self._poll()
        except AdapterError as exc:
            return AdapterResult(read_errors=1, note=str(exc))
        except Exception as exc:  # never crash the membrane
            return AdapterResult(read_errors=1, note=f"adapter error: {exc}")

    def _poll(self) -> AdapterResult:  # pragma: no cover - overridden
        raise NotImplementedError

    def close(self) -> None:
        self._closed = True

    def snapshot(self) -> Dict[str, Any]:
        return {"adapter": self.name, "source_id": self.config.source_id,
                "source_type": self.config.source_type,
                "closed": self._closed}

    # -- helpers for subclasses -------------------------------------------------

    def _too_large(self) -> bool:
        path = self.config.path
        if not path or not os.path.isfile(path):
            return False
        try:
            return os.path.getsize(path) > self.config.max_file_size_mb \
                * 1024 * 1024
        except OSError:
            return False

    def _make_event(self, **kwargs: Any) -> RawSensoryEvent:
        kwargs.setdefault("source_id", self.config.source_id)
        kwargs.setdefault("source_type", self.config.source_type)
        kwargs.setdefault("adapter_name", self.name)
        kwargs.setdefault("is_simulated", self.config.is_simulated)
        kwargs.setdefault("trust_level", self.config.trust_level)
        return RawSensoryEvent(**kwargs)
