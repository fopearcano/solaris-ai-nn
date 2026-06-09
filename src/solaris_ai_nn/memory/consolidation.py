"""Memory consolidation (stub).

In Solaris_Ai, repeated experience is gradually distilled into stabler
structure. This is a deliberate **stub** for that process: it summarises the
current trace and state memory without yet writing anything back into the
substrate. Phase 3 of the roadmap (persistent memory + Inner MAP coupling) will
turn this into a real consolidation step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .state_memory import StateMemory
from .trace_memory import TraceMemory


@dataclass
class ConsolidationSummary:
    """Read-only summary produced by a consolidation pass."""

    trace_length: int
    snapshot_count: int
    total_state_drift: float
    note: str = "stub: no write-back to substrate yet (see ROADMAP Phase 3)"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "trace_length": self.trace_length,
            "snapshot_count": self.snapshot_count,
            "total_state_drift": round(self.total_state_drift, 6),
            "note": self.note,
        }


def consolidate(trace: TraceMemory, state: StateMemory) -> ConsolidationSummary:
    """Summarise memory; does not yet modify any substrate (intentional stub)."""
    return ConsolidationSummary(
        trace_length=len(trace),
        snapshot_count=len(state),
        total_state_drift=state.total_drift(),
    )
