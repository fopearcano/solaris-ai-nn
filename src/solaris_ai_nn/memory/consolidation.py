"""Memory consolidation -- structural/statistical distillation of the trace.

In Solaris_Ai, repeated experience is gradually distilled into stabler structure
(``modules/memory_senses.py`` feeding the Inner MAP). Here that is done purely
*structurally*: counting repeated event patterns, absence-stimulus cycles, and
reaction feedback, and identifying stable action tendencies.

There is **no** LLM summarisation and **no** embeddings -- only counting and
simple sequence analysis over the recent trace. The output feeds the Inner MAP's
:class:`MemoryState`.

The original lightweight :func:`consolidate` (trace + state snapshots) is kept
for backwards compatibility; :class:`MemoryConsolidator` is the richer Phase-4
consolidation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .state_memory import StateMemory
from .trace_memory import TraceMemory

if TYPE_CHECKING:  # local import at call time to avoid an import cycle
    from ..inner_map.model import MemoryState


# --------------------------------------------------------------------------- #
# Backwards-compatible lightweight summary (Prompt 1)                          #
# --------------------------------------------------------------------------- #


@dataclass
class ConsolidationSummary:
    """Read-only summary produced by the original lightweight consolidation."""

    trace_length: int
    snapshot_count: int
    total_state_drift: float
    note: str = "lightweight summary; see MemoryConsolidator for full consolidation"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "trace_length": self.trace_length,
            "snapshot_count": self.snapshot_count,
            "total_state_drift": round(self.total_state_drift, 6),
            "note": self.note,
        }


def consolidate(trace: TraceMemory, state: StateMemory) -> ConsolidationSummary:
    """Summarise trace length + state-snapshot drift (lightweight)."""
    return ConsolidationSummary(
        trace_length=len(trace),
        snapshot_count=len(state),
        total_state_drift=state.total_drift(),
    )


# --------------------------------------------------------------------------- #
# Phase-4 structural consolidation                                            #
# --------------------------------------------------------------------------- #


@dataclass
class ConsolidationReport:
    """Structural consolidation of the recent trace window."""

    window_size: int
    events_considered: int
    kind_counts: Dict[str, int] = field(default_factory=dict)
    dominant_signal_type: Optional[str] = None
    last_signal_types: List[str] = field(default_factory=list)
    absence_count: int = 0
    absence_cycles: int = 0
    reaction_count: int = 0
    positive_reactions: int = 0
    negative_reactions: int = 0
    action_counts: Dict[str, int] = field(default_factory=dict)
    stable_action: Optional[str] = None
    stable_action_ratio: float = 0.0
    repeated_patterns: Dict[str, int] = field(default_factory=dict)
    summaries: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_size": self.window_size,
            "events_considered": self.events_considered,
            "kind_counts": self.kind_counts,
            "dominant_signal_type": self.dominant_signal_type,
            "last_signal_types": self.last_signal_types,
            "absence_count": self.absence_count,
            "absence_cycles": self.absence_cycles,
            "reaction_count": self.reaction_count,
            "positive_reactions": self.positive_reactions,
            "negative_reactions": self.negative_reactions,
            "action_counts": self.action_counts,
            "stable_action": self.stable_action,
            "stable_action_ratio": round(self.stable_action_ratio, 4),
            "repeated_patterns": self.repeated_patterns,
            "summaries": self.summaries,
        }


class MemoryConsolidator:
    """Counts repeated patterns / absence cycles / feedback over a trace window."""

    def consolidate(self, trace: TraceMemory, window_size: int = 100) -> ConsolidationReport:
        """Consolidate the last ``window_size`` trace records into a report."""
        records = trace.records[-window_size:] if window_size > 0 else list(trace.records)

        kind_counts: Counter[str] = Counter()
        action_counts: Counter[str] = Counter()
        signal_sequence: List[tuple[str, bool]] = []  # (kind, is_absence) in order
        reaction_valences: List[float] = []

        for rec in records:
            cat = rec.category
            data = rec.data
            if cat == "event":
                kind = str(data.get("kind", "Unknown"))
                is_abs = bool(data.get("is_absence", False))
                kind_counts[kind] += 1
                signal_sequence.append((kind, is_abs))
            elif cat == "signal":
                sig = data.get("signal", {}) or {}
                kind = str(sig.get("kind", "Unknown"))
                is_abs = bool(sig.get("is_absence", False))
                kind_counts[kind] += 1
                signal_sequence.append((kind, is_abs))
                if data.get("reaction") is not None:
                    reaction_valences.append(float(data["reaction"]))
            elif cat == "action":
                action_counts[str(data.get("action", "?"))] += 1
            elif cat == "reaction":
                reaction_valences.append(float(data.get("valence", 0.0)))

        # Absence cycles: maximal contiguous runs of absence stimuli.
        absence_count = sum(1 for _, a in signal_sequence if a)
        absence_cycles = 0
        prev_abs = False
        for _, is_abs in signal_sequence:
            if is_abs and not prev_abs:
                absence_cycles += 1
            prev_abs = is_abs

        dominant = kind_counts.most_common(1)[0][0] if kind_counts else None
        last_types = [k for k, _ in signal_sequence[-10:]]
        repeated = {k: c for k, c in kind_counts.items() if c > 1}

        pos = sum(1 for v in reaction_valences if v > 0)
        neg = sum(1 for v in reaction_valences if v < 0)

        stable_action = None
        stable_ratio = 0.0
        if action_counts:
            stable_action, top = action_counts.most_common(1)[0]
            total_actions = sum(action_counts.values())
            stable_ratio = top / total_actions if total_actions else 0.0

        summaries: List[str] = []
        if dominant:
            summaries.append(f"dominant recent signal: {dominant} ({kind_counts[dominant]}x)")
        if absence_cycles:
            summaries.append(f"{absence_cycles} absence cycle(s), {absence_count} absence stimuli")
        if reaction_valences:
            summaries.append(f"reactions: {pos} positive / {neg} negative of {len(reaction_valences)}")
        if stable_action:
            summaries.append(f"stable action tendency: {stable_action} ({stable_ratio:.0%})")
        if not summaries:
            summaries.append("no notable structure in the recent window yet")

        return ConsolidationReport(
            window_size=window_size,
            events_considered=len(records),
            kind_counts=dict(kind_counts),
            dominant_signal_type=dominant,
            last_signal_types=last_types,
            absence_count=absence_count,
            absence_cycles=absence_cycles,
            reaction_count=len(reaction_valences),
            positive_reactions=pos,
            negative_reactions=neg,
            action_counts=dict(action_counts),
            stable_action=stable_action,
            stable_action_ratio=stable_ratio,
            repeated_patterns=repeated,
            summaries=summaries,
        )

    def to_memory_state(self, report: ConsolidationReport) -> "MemoryState":
        """Convert a report into the Inner MAP's :class:`MemoryState`."""
        from ..inner_map.model import MemoryState  # local import: avoid cycle

        return MemoryState(
            trace_length=report.events_considered,
            last_signal_types=list(report.last_signal_types),
            dominant_recent_signal_type=report.dominant_signal_type,
            recent_absence_count=report.absence_count,
            recent_reaction_count=report.reaction_count,
            consolidated_summaries=list(report.summaries),
        )
