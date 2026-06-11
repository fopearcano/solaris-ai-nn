"""Consolidation policy -- what survives, at what resolution, and why.

A deterministic, low-compute priority ladder decides what stays hot, what
compresses to warm, what consolidates to cold, what fossilizes, and what
may be pruned. Identity, safety, prediction failures, Mysterium spikes,
habit changes, world-model phase changes, pruning events, restart gaps,
long stable patterns, and rare events are preserved in that order. No LLM
summarization, no human feedback -- keyword scoring over recorded events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .memory_layers import MemoryItem

# (priority rank, keywords) -- lower rank = preserved harder.
PRESERVATION_LADDER = (
    (1, ("identity", "continuity", "anchor")),
    (2, ("emergency", "safety", "boundary", "violation")),
    (3, ("prediction_failure", "prediction failure", "miss")),
    (4, ("mysterium", "unknown_pressure", "spike")),
    (5, ("habit_formed", "habit_collapse", "habit")),
    (6, ("world_model", "schema", "phase")),
    (7, ("pruning", "synthesis", "subtraction")),
    (8, ("restart", "gap", "checkpoint")),
    (9, ("stable", "pattern")),
    (10, ("rare", "first_", "novel")),
)


def preservation_rank(item: MemoryItem) -> int:
    """1..10 for ladder matches; 99 for routine events."""
    text = (item.kind + " " + str(item.content)).lower()
    for rank, keywords in PRESERVATION_LADDER:
        if any(keyword in text for keyword in keywords):
            return rank
    return 99


@dataclass
class CompressionReport:
    """What one consolidation pass did, traceably."""

    input_count: int = 0
    kept_hot: int = 0
    to_warm: int = 0
    to_cold: int = 0
    to_fossil: int = 0
    pruned: int = 0
    compression_ratio: float = 1.0
    evidence_summary: str = ""
    preserved_important: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ConsolidationDecision:
    """The sorted fate of one batch of memory items."""

    keep_hot: List[MemoryItem] = field(default_factory=list)
    to_warm: List[MemoryItem] = field(default_factory=list)
    to_cold: List[MemoryItem] = field(default_factory=list)
    to_fossil: List[MemoryItem] = field(default_factory=list)
    prune: List[MemoryItem] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"keep_hot": len(self.keep_hot),
                "to_warm": len(self.to_warm),
                "to_cold": len(self.to_cold),
                "to_fossil": len(self.to_fossil),
                "prune": len(self.prune),
                "reasons": list(self.reasons[:10])}


@dataclass
class ConsolidationPolicy:
    """Deterministic fate assignment plus application to the layers."""

    hot_keep_recent: int = 50  # the newest hot items always stay hot
    decisions_made: int = field(default=0, init=False)
    last_report: CompressionReport = field(
        default_factory=CompressionReport, init=False)

    def decide(self, hot_items: List[MemoryItem],
               context: Dict[str, Any] | None = None,
               ) -> ConsolidationDecision:
        ctx = dict(context or {})
        decision = ConsolidationDecision()
        recent = hot_items[-self.hot_keep_recent:]
        older = hot_items[:-self.hot_keep_recent] \
            if len(hot_items) > self.hot_keep_recent else []
        decision.keep_hot = list(recent)
        for item in older:
            rank = preservation_rank(item)
            if rank <= 2 or ctx.get("fossilize_all_important"):
                # Identity/safety events are fossil candidates outright.
                decision.to_fossil.append(item)
                decision.reasons.append(
                    f"preserved (rank {rank}): "
                    f"{item.evidence_summary[:60]}")
            elif rank <= 8:
                decision.to_cold.append(item)
                decision.reasons.append(
                    f"consolidated (rank {rank}): {item.kind}")
            else:
                decision.to_warm.append(item)
        self.decisions_made += 1
        return decision

    def apply(self, manager: Any,
              context: Dict[str, Any] | None = None,
              lifetime_s: float = 0.0) -> CompressionReport:
        """Decide over the manager's hot layer and move accordingly."""
        hot = list(manager.layers["hot"])
        decision = self.decide(hot, context)
        report = CompressionReport(input_count=len(hot),
                                   kept_hot=len(decision.keep_hot))
        if decision.to_warm:
            kinds = sorted({i.kind for i in decision.to_warm})
            summary = (f"{len(decision.to_warm)} routine events "
                       f"compressed (kinds: {', '.join(kinds[:5])})")
            manager.compress_to_warm(decision.to_warm, summary,
                                     lifetime_s=lifetime_s)
            report.to_warm = len(decision.to_warm)
            report.evidence_summary = summary
        for item in decision.to_cold:
            manager.compress_to_warm(
                [item], f"important event preserved: "
                        f"{item.evidence_summary[:80]}",
                kind="important_summary", lifetime_s=lifetime_s)
            report.to_cold += 1
            report.preserved_important.append(item.kind)
        for item in decision.to_fossil:
            manager.record_fossil(
                {"description": item.evidence_summary,
                 "kind": item.kind, "content": item.content},
                kind=item.kind, lifetime_s=lifetime_s)
            if item in manager.layers["hot"]:
                manager.layers["hot"].remove(item)
            report.to_fossil += 1
            report.preserved_important.append(item.kind)
        # Stored *items*: a warm batch is one summary, not N events.
        stored = (report.kept_hot + (1 if report.to_warm else 0)
                  + report.to_cold + report.to_fossil)
        report.compression_ratio = (round(stored
                                          / max(1, report.input_count), 4))
        self.last_report = report
        return report

    def snapshot(self) -> Dict[str, Any]:
        return {"decisions_made": self.decisions_made,
                "hot_keep_recent": self.hot_keep_recent,
                "last_report": self.last_report.to_dict(),
                "ladder": [{"rank": rank, "keywords": list(keywords)}
                           for rank, keywords in PRESERVATION_LADDER],
                "note": "deterministic keyword scoring; no LLM, no human "
                        "feedback, low compute"}
