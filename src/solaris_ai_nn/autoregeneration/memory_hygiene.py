"""Memory hygiene -- keep the layered memory from collapsing into entropy.

The :class:`MemoryHygieneManager` detects hot-layer over-budget,
warm/cold/fossil overgrowth, duplicate summaries, stale traces, and missing
evidence summaries, then proposes compaction / fossilization / archive.
Safety/boundary/emergency events are never compacted away, fossil memory is
append-first, and compression must preserve transformation evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .repair_actions import RepairAction, RepairActionType, make_repair

# Memory record kinds that may never be compacted away.
PROTECTED_KINDS = frozenset({
    "boundary_violation", "safety_incident", "emergency_stop",
    "policy_violation", "incident", "milestone",
})


@dataclass
class MemoryHygieneManager:
    """Detects memory degradation and proposes evidence-preserving repairs."""

    findings: List[Dict[str, Any]] = field(default_factory=list)

    def detect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        memory = (context or {}).get("memory") or {}
        over = list(memory.get("over_budget") or [])
        comp = memory.get("compression_ratio")
        duplicates = list(memory.get("duplicate_summaries") or [])
        stale = list(memory.get("stale_traces") or [])
        missing_summary = bool(memory.get("missing_evidence_summary"))
        result = {
            "over_budget": over,
            "compression_ratio": comp,
            "duplicate_summaries": len(duplicates),
            "stale_traces": len(stale),
            "missing_evidence_summary": missing_summary,
            "compression_loss_risk": (comp is not None
                                      and float(comp) > 0.95 and bool(over)),
        }
        self.findings.append(result)
        self.findings = self.findings[-50:]
        return result

    def propose(self, context: Dict[str, Any]) -> List[RepairAction]:
        detected = self.detect(context)
        actions: List[RepairAction] = []
        for layer in detected["over_budget"]:
            actions.append(make_repair(
                RepairActionType.COMPACT_MEMORY_LAYER, target_ref=str(layer),
                reason=f"layer {layer} over budget",
                expected_benefit="reduce memory bloat",
                preserve_protected=sorted(PROTECTED_KINDS)))
        if detected["over_budget"]:
            actions.append(make_repair(
                RepairActionType.REQUEST_CONSOLIDATION,
                target_ref="memory",
                reason="consolidate hot memory before it grows further",
                expected_benefit="fossilize/consolidate detail with "
                                 "evidence summaries preserved"))
        if detected["stale_traces"]:
            actions.append(make_repair(
                RepairActionType.ARCHIVE_OLD_TELEMETRY,
                target_ref="stale_traces",
                reason="stale traces present",
                expected_benefit="archive stale traces"))
        return actions

    @staticmethod
    def can_compact(record: Dict[str, Any]) -> bool:
        """Protected (safety/boundary/emergency/milestone) records stay."""
        kind = str(record.get("kind", "")).lower()
        return kind not in PROTECTED_KINDS

    def snapshot(self) -> Dict[str, Any]:
        return {
            "protected_kinds": sorted(PROTECTED_KINDS),
            "last_finding": self.findings[-1] if self.findings else None,
        }
