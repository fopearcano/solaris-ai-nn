"""Drift monitoring -- measuring plasticity without full retraining.

A long-running substrate should change *slowly and observably*. This module
tracks how much the readout weights move between checks, giving a single scalar
("drift") that experiments can watch to confirm the system is still adapting but
not thrashing. It does not modify anything; it only measures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from ..reservoir.readout import LinearReadout


def _flatten(readout: LinearReadout) -> List[float]:
    return [w for row in readout.weights for w in row]


@dataclass
class DriftMonitor:
    """Tracks Euclidean drift of readout weights between successive samples."""

    _last: Optional[List[float]] = field(default=None, repr=False)
    history: List[float] = field(default_factory=list)

    def sample(self, readout: LinearReadout) -> float:
        """Record current weights; return drift since the previous sample.

        The first sample returns 0.0 (no prior reference).
        """
        current = _flatten(readout)
        if self._last is None or len(self._last) != len(current):
            self._last = current
            self.history.append(0.0)
            return 0.0
        drift = math.sqrt(
            math.fsum((a - b) ** 2 for a, b in zip(current, self._last))
        )
        self._last = current
        self.history.append(drift)
        return drift

    def average_drift(self) -> float:
        """Mean drift over all samples (0.0 if none recorded)."""
        if not self.history:
            return 0.0
        return math.fsum(self.history) / len(self.history)
