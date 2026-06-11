"""Layered memory -- hot detail decays into warm summaries, cold schemas,
and fossil milestones; raw events never grow forever.

Hot memory holds full-detail recent events (bounded, minutes/hours). Warm
memory holds compressed trace summaries (days/weeks). Cold memory holds
consolidated schemas, stable habits, and persistent unknowns
(months/years). Fossil memory holds rare transformation milestones,
append-only on disk. Every movement between layers is audited, and
nothing leaves hot memory without a summary that preserves its evidence.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class MemoryLayer:
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    FOSSIL = "fossil"

    ALL = (HOT, WARM, COLD, FOSSIL)

    # In-memory budgets (fossil persists append-only; the list is a tail).
    BUDGETS = {HOT: 500, WARM: 300, COLD: 200, FOSSIL: 100}


@dataclass
class MemoryItem:
    """One entry in one layer, with its provenance."""

    layer: str
    kind: str = "event"
    content: Dict[str, Any] = field(default_factory=dict)
    evidence_summary: str = ""
    source_count: int = 1  # how many raw events this item stands for
    importance: float = 0.0
    created_at_lifetime_s: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LayeredMemoryState:
    """Counts and ratios across the four layers."""

    hot_count: int = 0
    warm_count: int = 0
    cold_count: int = 0
    fossil_count: int = 0
    raw_events_seen: int = 0
    compressed_events: int = 0
    movements: int = 0
    over_budget: List[str] = field(default_factory=list)

    def compression_ratio(self) -> Optional[float]:
        if not self.raw_events_seen:
            return None
        stored = (self.hot_count + self.warm_count + self.cold_count
                  + self.fossil_count)
        return round(stored / self.raw_events_seen, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "compression_ratio": self.compression_ratio()}


@dataclass
class MemoryLayerManager:
    """Owns the four layers; every movement leaves an audit row."""

    state_dir: Optional[Union[str, Path]] = None
    budgets: Dict[str, int] = field(
        default_factory=lambda: dict(MemoryLayer.BUDGETS))

    def __post_init__(self) -> None:
        self.layers: Dict[str, List[MemoryItem]] = {
            layer: [] for layer in MemoryLayer.ALL}
        self.movement_log: List[Dict[str, Any]] = []
        self.raw_events_seen = 0
        self.compressed_events = 0
        self.fossil_path = (Path(self.state_dir) / "fossil_memory.jsonl"
                            if self.state_dir else None)

    # -- intake ---------------------------------------------------------------------

    def add_hot(self, content: Dict[str, Any], kind: str = "event",
                importance: float = 0.0,
                lifetime_s: float = 0.0) -> MemoryItem:
        item = MemoryItem(layer=MemoryLayer.HOT, kind=kind,
                          content=dict(content), importance=importance,
                          evidence_summary=str(content)[:120],
                          created_at_lifetime_s=lifetime_s)
        self.layers[MemoryLayer.HOT].append(item)
        self.raw_events_seen += 1
        self._enforce_budget(MemoryLayer.HOT)
        return item

    # -- movement (always audited, always evidence-preserving) ---------------------------

    def compress_to_warm(self, items: List[MemoryItem], summary: str,
                         kind: str = "trace_summary",
                         lifetime_s: float = 0.0) -> MemoryItem:
        """N hot items become one warm summary; the hot items retire."""
        if not summary:
            raise ValueError("compression must produce an evidence "
                             "summary; silent deletion is forbidden")
        warm = MemoryItem(
            layer=MemoryLayer.WARM, kind=kind,
            content={"summary": summary,
                     "kinds": sorted({i.kind for i in items}),
                     "span": [min((i.created_at_lifetime_s
                                   for i in items), default=lifetime_s),
                              lifetime_s]},
            evidence_summary=summary[:200],
            source_count=sum(i.source_count for i in items) or 1,
            importance=max((i.importance for i in items), default=0.0),
            created_at_lifetime_s=lifetime_s)
        for item in items:
            if item in self.layers[MemoryLayer.HOT]:
                self.layers[MemoryLayer.HOT].remove(item)
        self.layers[MemoryLayer.WARM].append(warm)
        self.compressed_events += len(items)
        self._record_movement(MemoryLayer.HOT, MemoryLayer.WARM,
                              len(items), summary)
        self._enforce_budget(MemoryLayer.WARM)
        return warm

    def consolidate_to_cold(self, items: List[MemoryItem], schema: str,
                            kind: str = "schema",
                            lifetime_s: float = 0.0) -> MemoryItem:
        """Warm summaries become one cold schema."""
        if not schema:
            raise ValueError("consolidation must produce a schema "
                             "summary")
        cold = MemoryItem(
            layer=MemoryLayer.COLD, kind=kind,
            content={"schema": schema,
                     "from_summaries": [i.evidence_summary[:80]
                                        for i in items[:5]]},
            evidence_summary=schema[:200],
            source_count=sum(i.source_count for i in items) or 1,
            importance=max((i.importance for i in items), default=0.5),
            created_at_lifetime_s=lifetime_s)
        for item in items:
            if item in self.layers[MemoryLayer.WARM]:
                self.layers[MemoryLayer.WARM].remove(item)
        self.layers[MemoryLayer.COLD].append(cold)
        self._record_movement(MemoryLayer.WARM, MemoryLayer.COLD,
                              len(items), schema)
        self._enforce_budget(MemoryLayer.COLD)
        return cold

    def record_fossil(self, content: Dict[str, Any],
                      kind: str = "milestone",
                      lifetime_s: float = 0.0) -> MemoryItem:
        """Append-only: rare transformation milestones, kept indefinitely."""
        fossil = MemoryItem(
            layer=MemoryLayer.FOSSIL, kind=kind, content=dict(content),
            evidence_summary=str(content.get("description",
                                             content))[:200],
            importance=1.0, created_at_lifetime_s=lifetime_s)
        self.layers[MemoryLayer.FOSSIL].append(fossil)
        # The on-disk fossil record is append-only; the in-memory list is
        # only a bounded tail of it.
        self.layers[MemoryLayer.FOSSIL] = \
            self.layers[MemoryLayer.FOSSIL][-self.budgets[
                MemoryLayer.FOSSIL]:]
        if self.fossil_path is not None:
            self.fossil_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fossil_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(fossil.to_dict(), default=str) + "\n")
        self._record_movement("event", MemoryLayer.FOSSIL, 1,
                              fossil.evidence_summary)
        return fossil

    def _enforce_budget(self, layer: str) -> None:
        budget = self.budgets[layer]
        overflow = len(self.layers[layer]) - budget
        if overflow <= 0:
            return
        if layer == MemoryLayer.HOT:
            # Hot overflow is auto-compressed, never silently dropped.
            victims = self.layers[layer][:overflow]
            summary = (f"auto-compressed {len(victims)} overflowing hot "
                       f"events; kinds: "
                       f"{sorted({v.kind for v in victims})}")
            self.compress_to_warm(victims, summary,
                                  kind="overflow_summary")
        else:
            # Warm/cold evict lowest-importance items into a tombstone
            # row in the movement log (evidence summary preserved).
            self.layers[layer].sort(key=lambda i: i.importance)
            victims = self.layers[layer][:overflow]
            self.layers[layer] = self.layers[layer][overflow:]
            for victim in victims:
                self._record_movement(layer, "pruned", 1,
                                      victim.evidence_summary)

    def _record_movement(self, from_layer: str, to_layer: str,
                         count: int, summary: str) -> None:
        self.movement_log.append({
            "from": from_layer, "to": to_layer, "count": count,
            "evidence_summary": str(summary)[:160],
            "timestamp": time.time()})
        self.movement_log = self.movement_log[-300:]

    # -- views --------------------------------------------------------------------

    def over_budget_layers(self) -> List[str]:
        return [layer for layer in MemoryLayer.ALL
                if len(self.layers[layer]) > self.budgets[layer]]

    def state(self) -> LayeredMemoryState:
        return LayeredMemoryState(
            hot_count=len(self.layers[MemoryLayer.HOT]),
            warm_count=len(self.layers[MemoryLayer.WARM]),
            cold_count=len(self.layers[MemoryLayer.COLD]),
            fossil_count=len(self.layers[MemoryLayer.FOSSIL]),
            raw_events_seen=self.raw_events_seen,
            compressed_events=self.compressed_events,
            movements=len(self.movement_log),
            over_budget=self.over_budget_layers())

    def snapshot(self) -> Dict[str, Any]:
        return {
            **self.state().to_dict(),
            "budgets": dict(self.budgets),
            "fossil_path": (str(self.fossil_path)
                            if self.fossil_path else None),
            "recent_movements": self.movement_log[-5:],
            "note": "raw events never grow forever; nothing leaves a "
                    "layer without an evidence summary",
        }
