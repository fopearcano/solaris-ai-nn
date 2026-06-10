"""SignalMirror -- read-only mirror of observed Solaris signals.

Every signal the sidecar observes is mirrored here for observability and
replay: original metadata (type/id/origin), the adapted canonical signal, and a
*summary* of the encoded vector (norm + length -- never the full vector unless
``full_payloads=True``). The mirror NEVER mutates the original Solaris signals;
it stores its own derived records only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from pathlib import Path


def _summarise_payload(value: Any, limit: int = 80) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


@dataclass
class MirroredSignal:
    """One mirrored observation (derived data only; the original is untouched)."""

    timestamp: float
    raw_type: str
    raw_id: Optional[Any]
    raw_origin: Optional[str]
    raw_summary: str
    adapted_kind: str
    adapted_summary: Dict[str, Any]
    vector_len: int = 0
    vector_norm: float = 0.0
    vector: Optional[List[float]] = None  # only kept in full_payloads mode

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "timestamp": self.timestamp,
            "raw_type": self.raw_type,
            "raw_id": self.raw_id,
            "raw_origin": self.raw_origin,
            "raw_summary": self.raw_summary,
            "adapted_kind": self.adapted_kind,
            "adapted_summary": self.adapted_summary,
            "vector_len": self.vector_len,
            "vector_norm": self.vector_norm,
        }
        if self.vector is not None:
            data["vector"] = self.vector
        return data


@dataclass
class SignalMirror:
    """Bounded, filterable store of mirrored signal observations.

    Args:
        capacity: Max mirrored records kept in memory (oldest dropped).
        allowed_types: Only mirror these signal kinds (None = all).
        full_payloads: Keep full encoded vectors (off by default: summaries only).
    """

    capacity: int = 5_000
    allowed_types: Optional[List[str]] = None
    full_payloads: bool = False
    records: List[MirroredSignal] = field(default_factory=list)
    skipped: int = 0

    def mirror(self, raw_signal: Any, adapted_signal: Any,
               encoded_vector: Optional[Sequence[float]] = None) -> Optional[MirroredSignal]:
        """Mirror one observation; returns the record (or None if filtered)."""
        kind = getattr(adapted_signal, "kind", type(adapted_signal).__name__)
        if self.allowed_types is not None and kind not in self.allowed_types:
            self.skipped += 1
            return None

        vector_len = 0
        vector_norm = 0.0
        kept_vector: Optional[List[float]] = None
        if encoded_vector is not None:
            vec = [float(x) for x in encoded_vector]
            vector_len = len(vec)
            vector_norm = sum(x * x for x in vec) ** 0.5
            if self.full_payloads:
                kept_vector = vec

        record = MirroredSignal(
            timestamp=time.time(),
            raw_type=type(raw_signal).__name__,
            raw_id=getattr(raw_signal, "id", None),
            raw_origin=getattr(raw_signal, "origin", None),
            raw_summary=_summarise_payload(getattr(raw_signal, "payload", raw_signal)),
            adapted_kind=kind,
            adapted_summary={
                "payload": _summarise_payload(getattr(adapted_signal, "payload", None)),
                "intensity": float(getattr(adapted_signal, "intensity", 0.0) or 0.0),
                "valence": float(getattr(adapted_signal, "valence", 0.0) or 0.0),
                "is_absence": bool(getattr(adapted_signal, "is_absence", False)),
            },
            vector_len=vector_len,
            vector_norm=vector_norm,
            vector=kept_vector,
        )
        self.records.append(record)
        if len(self.records) > self.capacity:
            self.records = self.records[-self.capacity:]
        return record

    # -- inspection -----------------------------------------------------------

    def tail(self, n: int) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records[-n:]]

    def count_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self.records:
            counts[r.adapted_kind] = counts.get(r.adapted_kind, 0) + 1
        return counts

    def __len__(self) -> int:
        return len(self.records)

    def to_jsonl(self, path: Union[str, Path]) -> int:
        """Export all mirrored records to a JSONL file; returns the row count."""
        from ..runtime.persistence import JsonlWriter  # local: avoid cycles

        with JsonlWriter(path) as writer:
            for r in self.records:
                writer.write(r.to_dict())
        return len(self.records)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "mirrored": len(self.records),
            "skipped": self.skipped,
            "by_type": self.count_by_type(),
            "capacity": self.capacity,
            "full_payloads": self.full_payloads,
            "allowed_types": list(self.allowed_types) if self.allowed_types else None,
        }
