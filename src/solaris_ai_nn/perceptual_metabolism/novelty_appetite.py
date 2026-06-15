"""Novelty appetite -- want the new, but don't chase noise forever.

A :class:`NoveltyAppetiteRegulator` tracks how much novelty was consumed, how much
of it converted into invariants (productive) versus stayed noise (unproductive),
and whether novelty is fatigued or starved. Recurring novelty should become a
rhythm/invariant candidate; unproductive novelty should be deprioritised; and the
appetite interacts with source reliability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class NoveltyAppetiteState:
    novelty_consumed: float = 0.0
    novelty_fatigue: float = 0.0
    novelty_starvation: float = 0.0
    overfitting_risk: float = 0.0
    novelty_to_invariant_rate: float = 0.0
    novelty_to_noise_ratio: float = 0.0
    recommendation: str = "balanced"

    def to_dict(self) -> Dict[str, Any]:
        return {**{k: (round(v, 4) if isinstance(v, float) else v)
                   for k, v in self.__dict__.items()},
                "note": "novelty appetite should not chase noise forever"}


@dataclass
class NoveltyAppetiteRegulator:
    """Regulates the appetite for novelty against productivity and reliability."""

    _consumed: float = field(default=0.0, init=False)
    _ticks: int = field(default=0, init=False)

    def update(self, sensorium: Any, *, field_state: Any = None,
               ) -> NoveltyAppetiteState:
        if field_state is None and hasattr(sensorium, "sensory_field"):
            field_state = sensorium.sensory_field.state()
        novelty = getattr(field_state, "novelty_pressure", 0.0)
        noise = getattr(field_state, "noise_pressure", 0.0)
        self._consumed += novelty
        self._ticks += 1

        invariants = len(getattr(sensorium, "invariants", None).candidates) \
            if hasattr(sensorium, "invariants") else 0
        # Conversion: invariants formed relative to novelty consumed.
        conversion = (invariants / self._consumed) if self._consumed > 0 else 0.0
        noise_ratio = noise / (novelty + 1e-6)
        # Fatigue grows when novelty is sustained-high; starvation when near 0.
        fatigue = min(1.0, max(0.0, self._consumed / max(1, self._ticks) - 0.5))
        starvation = 1.0 if novelty < 0.05 else 0.0
        # Overfitting risk: high novelty but low conversion to invariants.
        overfit = min(1.0, novelty * (1.0 - min(1.0, conversion)))

        if starvation > 0.5:
            rec = "raise_novelty_appetite"
        elif noise_ratio > 1.5 or fatigue > 0.5:
            rec = "lower_novelty_appetite_chasing_noise"
        elif conversion > 0.3:
            rec = "novelty_is_productive_keep"
        else:
            rec = "balanced"
        return NoveltyAppetiteState(
            novelty_consumed=self._consumed, novelty_fatigue=fatigue,
            novelty_starvation=starvation, overfitting_risk=overfit,
            novelty_to_invariant_rate=round(min(1.0, conversion), 4),
            novelty_to_noise_ratio=round(min(5.0, noise_ratio), 4),
            recommendation=rec)
