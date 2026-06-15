"""Perceptual baseline -- what counts as *normal* for each receptor/modality.

A :class:`PerceptualBaseline` is learned gradually (a slow running estimate, never
overwritten in one step). When the world drifts far enough from the learned
normal, a :class:`BaselineShift` is emitted -- and a baseline shift is itself a
first-class stimulus.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PerceptualBaseline:
    """The learned normal range / rhythm / silence for one receptor."""

    receptor_id: str
    modality: str
    mean_intensity: float = 0.0
    intensity_var: float = 0.0
    noise_floor: float = 0.0
    normal_rhythm: Optional[float] = None
    normal_silence: float = 0.0
    normal_recurrence: float = 0.0
    sample_count: int = 0

    @property
    def std_intensity(self) -> float:
        return math.sqrt(max(0.0, self.intensity_var))

    @property
    def low(self) -> float:
        return self.mean_intensity - 2.0 * self.std_intensity

    @property
    def high(self) -> float:
        return self.mean_intensity + 2.0 * self.std_intensity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receptor_id": self.receptor_id,
            "modality": self.modality,
            "mean_intensity": self.mean_intensity,
            "std_intensity": self.std_intensity,
            "noise_floor": self.noise_floor,
            "normal_rhythm": self.normal_rhythm,
            "normal_silence": self.normal_silence,
            "normal_recurrence": self.normal_recurrence,
            "sample_count": self.sample_count,
        }


@dataclass
class BaselineShift:
    """A detected, persistent shift in a receptor's baseline."""

    receptor_id: str
    modality: str
    field_name: str
    old_value: float
    new_value: float
    magnitude: float

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class BaselineEstimator:
    """Maintains gradually-learned baselines and detects baseline shifts."""

    # The learning rate is deliberately small: baselines move slowly.
    learn_rate: float = 0.1
    shift_threshold: float = 0.5
    baselines: Dict[str, PerceptualBaseline] = field(default_factory=dict)

    def update(self, receptor_id: str, modality: str, intensity: float,
               *, silence: float = 0.0) -> Optional[BaselineShift]:
        base = self.baselines.get(receptor_id)
        if base is None:
            base = PerceptualBaseline(receptor_id=receptor_id, modality=modality,
                                      mean_intensity=intensity,
                                      noise_floor=intensity)
            base.sample_count = 1
            self.baselines[receptor_id] = base
            return None
        old_mean = base.mean_intensity
        # Welford-ish slow update; the mean never jumps to the new value.
        delta = intensity - base.mean_intensity
        base.mean_intensity += self.learn_rate * delta
        base.intensity_var = (1 - self.learn_rate) * (
            base.intensity_var + self.learn_rate * delta * delta)
        base.noise_floor = min(base.noise_floor, intensity) \
            if base.sample_count > 1 else intensity
        base.normal_silence = (1 - self.learn_rate) * base.normal_silence \
            + self.learn_rate * silence
        base.sample_count += 1
        magnitude = abs(base.mean_intensity - old_mean) / (abs(old_mean) + 1e-6)
        if base.sample_count > 5 and magnitude >= self.shift_threshold:
            return BaselineShift(receptor_id=receptor_id, modality=modality,
                                 field_name="mean_intensity",
                                 old_value=old_mean,
                                 new_value=base.mean_intensity,
                                 magnitude=magnitude)
        return None

    def get(self, receptor_id: str) -> Optional[PerceptualBaseline]:
        return self.baselines.get(receptor_id)

    def all_baselines(self) -> List[PerceptualBaseline]:
        return list(self.baselines.values())

    def snapshot(self) -> Dict[str, Any]:
        return {"baseline_count": len(self.baselines),
                "baselines": [b.to_dict() for b in self.baselines.values()]}
