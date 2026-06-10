"""EnergyModel -- a simple, deterministic simulated metabolism.

Energy is the body's internal need: movement costs it, rest restores it, low
energy emits an internal Stimulus (via EnergySensor), and exhaustion blocks
costly actions. It is a plain bounded scalar -- a *simulated need*, not hunger.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class EnergyModel:
    """Bounded energy with rest recovery and an exhaustion floor."""

    max_energy: float = 10.0
    energy: float = 10.0
    low_threshold: float = 3.0
    rest_recovery: float = 1.5
    exhaustion_floor: float = 1.0
    spent_total: float = 0.0
    exhaustion_events: int = 0

    @property
    def exhausted(self) -> bool:
        """Below the floor, any positive-cost action is blocked."""
        return self.energy < self.exhaustion_floor

    @property
    def is_low(self) -> bool:
        return self.energy <= self.low_threshold

    def can_afford(self, cost: float) -> bool:
        if cost <= 0.0:
            return True
        if self.exhausted:
            return False
        return self.energy >= cost

    def spend(self, cost: float) -> bool:
        """Deduct ``cost`` if affordable; returns False (and no deduction) if not."""
        if not self.can_afford(cost):
            return False
        was_exhausted = self.exhausted
        self.energy = max(0.0, self.energy - cost)
        self.spent_total += cost
        if self.exhausted and not was_exhausted:
            self.exhaustion_events += 1
        return True

    def rest(self) -> float:
        """Recover energy; returns the amount actually recovered."""
        before = self.energy
        self.energy = min(self.max_energy, self.energy + self.rest_recovery)
        return self.energy - before

    def snapshot(self) -> Dict[str, Any]:
        return {
            "energy": round(self.energy, 4),
            "max_energy": self.max_energy,
            "low_threshold": self.low_threshold,
            "rest_recovery": self.rest_recovery,
            "is_low": self.is_low,
            "exhausted": self.exhausted,
            "spent_total": round(self.spent_total, 4),
            "exhaustion_events": self.exhaustion_events,
        }
