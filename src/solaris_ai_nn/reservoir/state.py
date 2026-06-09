"""Reservoir state snapshots.

A tiny value type used by :mod:`solaris_ai_nn.memory` to record the reservoir's
internal state at intervals, so a long-running experiment leaves a trail of how
its "nervous substrate" evolved without coupling memory to the ESN class.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

from ..utils.math import Vector, norm


@dataclass
class StateSnapshot:
    """A point-in-time copy of reservoir state plus light summary stats."""

    step: int
    state: Vector
    timestamp: float = field(default_factory=time.time)

    @property
    def energy(self) -> float:
        """L2 norm of the state -- a coarse "activation level" metric."""
        return norm(self.state)


def snapshot_state(step: int, state: Vector) -> StateSnapshot:
    """Build a :class:`StateSnapshot`, copying the state defensively."""
    return StateSnapshot(step=step, state=list(state))


def state_drift(a: StateSnapshot, b: StateSnapshot) -> float:
    """Euclidean distance between two snapshots' states (state plasticity)."""
    if len(a.state) != len(b.state):
        raise ValueError("snapshot dimensionality mismatch")
    return norm([x - y for x, y in zip(a.state, b.state)])
