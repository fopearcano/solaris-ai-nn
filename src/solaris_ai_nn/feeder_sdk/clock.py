"""Clock helpers -- seedable, reproducible timing for simulated feeders.

These help a *feeder* (outside Solaris) schedule events with realistic timing:
:class:`FeederClock` advances simulated time, :class:`TickSchedule` yields tick
times at an interval, and :class:`JitterModel` adds reproducible jitter. They are
feeder-simulation tools, not part of Solaris cognition.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class FeederClock:
    """A simple monotonic simulated clock for a feeder."""

    start: float = 0.0
    step: float = 1.0
    _now: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self._now = self.start

    def now(self) -> float:
        return self._now

    def tick(self) -> float:
        self._now += self.step
        return self._now


@dataclass
class TickSchedule:
    """Yields tick times at a fixed interval, up to a bound."""

    interval: float = 1.0
    count: int = 10
    start: float = 0.0

    def times(self) -> List[float]:
        return [round(self.start + i * self.interval, 6)
                for i in range(max(0, self.count))]


@dataclass
class JitterModel:
    """Adds reproducible, bounded jitter to a timestamp (seedable)."""

    amplitude: float = 0.2
    seed: int = 7
    _rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def apply(self, t: float) -> float:
        return round(t + self._rng.uniform(-self.amplitude, self.amplitude), 6)

    def reset(self) -> None:
        self._rng = random.Random(self.seed)
