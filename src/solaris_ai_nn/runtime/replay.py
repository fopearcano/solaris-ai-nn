"""EventReplay -- feed a recorded trace back into a bridge.

A long-running substrate is only studyable if its behaviour is reproducible
enough to compare runs. The runner writes every processed input signal (and any
reaction valence) to ``trace_events.jsonl`` via
:meth:`TraceMemory.record_signal`. This module reads that trace and replays it
into a fresh :class:`SolarisNeuralBridge`.

Because the bridge is deterministic given its seed (fixed reservoir matrices,
seeded exploration RNG) and the trace fixes the exact input sequence, two
replays into two identically-seeded fresh bridges produce identical telemetry --
which is what the tests assert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..signals import canonical as C
from .persistence import read_jsonl

if TYPE_CHECKING:  # Only for type hints; the bridge is passed in by the caller.
    from ..bridges.neural_bridge import SolarisNeuralBridge


@dataclass
class EventReplay:
    """Load a recorded signal trace and replay it into a bridge."""

    rows: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load_trace(cls, path: Union[str, Path]) -> "EventReplay":
        """Load ``trace_events.jsonl`` into a replay object (empty if absent)."""
        if not Path(path).exists():
            return cls(rows=[])
        return cls(rows=list(read_jsonl(path)))

    def signal_rows(self) -> List[Dict[str, Any]]:
        """Only the replayable signal rows (category == 'signal')."""
        return [r for r in self.rows if r.get("category") == "signal"]

    def replay_into_bridge(
        self,
        bridge: SolarisNeuralBridge,
        max_events: Optional[int] = None,
    ) -> int:
        """Replay recorded signals (and reactions) into ``bridge``.

        Args:
            bridge: Target bridge (typically freshly constructed for determinism).
            max_events: Cap on the number of signal rows replayed (None = all).

        Returns:
            The number of signal rows replayed.
        """
        rows = self.signal_rows()
        if max_events is not None:
            rows = rows[:max_events]
        for row in rows:
            signal = row.get("signal")
            if signal is None:
                continue
            bridge.process(signal)  # the bridge's adapter accepts a dict directly
            reaction = row.get("reaction")
            if reaction is not None:
                bridge.react(C.Reaction(valence=float(reaction)))
        return len(rows)
