"""State memory -- periodic snapshots of the reservoir's internal state.

Records the reservoir's "nervous substrate" at intervals so a long run leaves a
trail of how its internal state evolved. Bounded in size; snapshots are cheap
copies, not full history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..reservoir.state import StateSnapshot, snapshot_state, state_drift
from ..utils.math import Vector


@dataclass
class StateMemory:
    """Holds reservoir-state snapshots taken every ``interval`` steps.

    Args:
        interval: Take a snapshot every N steps.
        capacity: Max snapshots retained (oldest dropped beyond this).
    """

    interval: int = 25
    capacity: int = 1_000
    snapshots: List[StateSnapshot] = field(default_factory=list)

    def maybe_snapshot(self, step: int, state: Vector) -> bool:
        """Snapshot the state if ``step`` lands on the interval.

        Returns True if a snapshot was taken.
        """
        if self.interval <= 0 or step % self.interval != 0:
            return False
        self.snapshots.append(snapshot_state(step, state))
        if len(self.snapshots) > self.capacity:
            self.snapshots = self.snapshots[-self.capacity :]
        return True

    def total_drift(self) -> float:
        """Sum of state drift between consecutive snapshots (state plasticity)."""
        return sum(
            state_drift(a, b)
            for a, b in zip(self.snapshots, self.snapshots[1:])
        )

    def __len__(self) -> int:
        return len(self.snapshots)
