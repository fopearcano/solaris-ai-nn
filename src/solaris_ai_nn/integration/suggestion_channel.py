"""NeuralSuggestion + SuggestionChannel -- the only outbound path.

The sidecar's entire output is suggestions. A :class:`NeuralSuggestion` is a
clearly-labelled proposal (``committed`` is ``False`` by construction and the
channel refuses anything claiming otherwise); Solaris_Ai decides what, if
anything, to do with it. When publishing is enabled and a bus is attached, the
suggestion object itself is published -- never a Solaris ``Action``, never
anything that looks committed.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Suggestion types.
DESIRE_SUGGESTION = "DesireSuggestion"
ACTION_SUGGESTION = "ActionSuggestion"
MODULATION_SUGGESTION = "ModulationSuggestion"
PLASTICITY_SUGGESTION = "PlasticitySuggestion"

SUGGESTION_TYPES = frozenset({
    DESIRE_SUGGESTION, ACTION_SUGGESTION, MODULATION_SUGGESTION,
    PLASTICITY_SUGGESTION,
})


@dataclass
class NeuralSuggestion:
    """A proposal from the NN substrate. Never a committed action.

    ``committed`` defaults to (and must remain) ``False``; the channel rejects
    any suggestion claiming to be committed as unsafe.
    """

    suggested_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    substrate_type: str = "unknown"
    substrate_summary: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    source_signal_id: Optional[Any] = None
    safety_status: str = "ok"
    committed: bool = False
    suggestion_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    # Marker so observers (and our own connector) can recognise these objects.
    kind: str = "NeuralSuggestion"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "timestamp": self.timestamp,
            "kind": self.kind,
            "suggested_type": self.suggested_type,
            "payload": dict(self.payload),
            "confidence": self.confidence,
            "substrate_type": self.substrate_type,
            "substrate_summary": dict(self.substrate_summary),
            "reason": self.reason,
            "source_signal_id": self.source_signal_id,
            "safety_status": self.safety_status,
            "committed": self.committed,
        }


@dataclass
class SuggestionChannel:
    """Stores suggestions and (optionally) publishes them to a bus.

    Args:
        bus: Optional Solaris_Ai-like bus with ``publish(obj)``.
        publish_enabled: Master switch; off => store-only.
        capacity: Max suggestions retained in memory.
    """

    bus: Any = None
    publish_enabled: bool = True
    capacity: int = 2_000
    suggestions: List[NeuralSuggestion] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    published_count: int = 0

    # -- intake ---------------------------------------------------------------

    def submit(self, suggestion: NeuralSuggestion, publish: bool = True) -> bool:
        """Store a suggestion and optionally publish it. Returns published?.

        Unsafe suggestions (unknown type, or anything claiming ``committed``)
        are rejected outright and recorded in :attr:`rejected`.
        """
        if suggestion.committed:
            self.reject(suggestion, "committed suggestions are forbidden: the "
                                    "NN sidecar has no action authority")
            return False
        if suggestion.suggested_type not in SUGGESTION_TYPES:
            self.reject(suggestion, f"unknown suggestion type "
                                    f"{suggestion.suggested_type!r}")
            return False

        self.suggestions.append(suggestion)
        if len(self.suggestions) > self.capacity:
            self.suggestions = self.suggestions[-self.capacity:]

        if publish and self.publish_enabled and self.bus is not None:
            return self._publish(suggestion)
        return False

    def reject(self, suggestion: NeuralSuggestion, reason: str) -> None:
        """Record a suggestion as rejected/unsafe (it is not stored as valid)."""
        suggestion.safety_status = f"rejected: {reason}"
        self.rejected.append({**suggestion.to_dict(), "rejection_reason": reason})
        if len(self.rejected) > self.capacity:
            self.rejected = self.rejected[-self.capacity:]

    def _publish(self, suggestion: NeuralSuggestion) -> bool:
        publish = getattr(self.bus, "publish", None)
        if not callable(publish):
            return False
        try:
            result = publish(suggestion)
        except Exception as exc:
            suggestion.safety_status = f"publish failed: {exc}"
            return False
        if hasattr(result, "__await__"):
            # Async bus with no running loop here: we cannot safely fire and
            # forget a coroutine. Close it and record the suggestion as stored
            # but unpublished, rather than leaking a never-awaited coroutine.
            result.close()
            suggestion.safety_status = "stored only (async bus needs a running loop)"
            return False
        self.published_count += 1
        return True

    # -- inspection -----------------------------------------------------------

    def last(self, n: int = 5) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self.suggestions[-n:]]

    def confidence_distribution(self) -> Dict[str, Any]:
        """min / max / mean plus 0.2-wide histogram buckets."""
        values = [s.confidence for s in self.suggestions]
        if not values:
            return {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "buckets": {}}
        buckets: Dict[str, int] = {}
        for v in values:
            lo = min(int(v / 0.2), 4) * 0.2
            key = f"{lo:.1f}-{lo + 0.2:.1f}"
            buckets[key] = buckets.get(key, 0) + 1
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "buckets": buckets,
        }

    def to_jsonl(self, path: Union[str, Path]) -> int:
        """Export stored suggestions to JSONL; returns the row count."""
        from ..runtime.persistence import JsonlWriter  # local: avoid cycles

        with JsonlWriter(path) as writer:
            for s in self.suggestions:
                writer.write(s.to_dict())
        return len(self.suggestions)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "stored": len(self.suggestions),
            "published": self.published_count,
            "rejected": len(self.rejected),
            "publish_enabled": self.publish_enabled,
            "bus_attached": self.bus is not None,
            "confidence": self.confidence_distribution(),
            "last": self.last(3),
        }
