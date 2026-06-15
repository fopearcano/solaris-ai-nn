"""Noise helpers -- seedable, reproducible environmental flux for feeders.

These let a *feeder* (outside Solaris) produce realistic flux:
:class:`FeatureNoiseModel` perturbs values, :class:`DropoutModel` drops events
(silence / missing-expected), :class:`BurstModel` produces bursts, and
:class:`DriftModel` adds slow baseline drift. All are seedable and reproducible.
They are feeder-simulation tools, not part of Solaris cognition.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class FeatureNoiseModel:
    """Adds bounded Gaussian-ish noise to a feature value (seedable)."""

    sigma: float = 0.05
    seed: int = 7
    _rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def apply(self, value: float) -> float:
        return round(value + self._rng.gauss(0.0, self.sigma), 6)

    def reset(self) -> None:
        self._rng = random.Random(self.seed)


@dataclass
class DropoutModel:
    """Drops events with a fixed probability (silence / missing expected)."""

    probability: float = 0.2
    seed: int = 7
    _rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def drop(self) -> bool:
        return self._rng.random() < self.probability

    def reset(self) -> None:
        self._rng = random.Random(self.seed)


@dataclass
class BurstModel:
    """Occasionally multiplies a value to simulate a burst (seedable)."""

    probability: float = 0.15
    gain: float = 2.5
    seed: int = 7
    _rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def apply(self, value: float) -> float:
        if self._rng.random() < self.probability:
            return round(value * self.gain, 6)
        return value

    def reset(self) -> None:
        self._rng = random.Random(self.seed)


@dataclass
class DriftModel:
    """Adds a slow, accumulating drift to a baseline (deterministic)."""

    rate: float = 0.01
    _accumulated: float = field(default=0.0, init=False)

    def apply(self, value: float) -> float:
        self._accumulated += self.rate
        return round(value + self._accumulated, 6)

    def reset(self) -> None:
        self._accumulated = 0.0
