"""Continuous sensory field -- the organism's perceptual state, not an event list.

The :class:`SensoryField` is the *current* organismic perceptual state. It is
continuous across ticks: its pressures (field, noise, absence, novelty, rhythm,
cross-modal, uncertainty) persist and decay rather than being recomputed from
scratch, and it is what drives Push generation and attention. A sensory field is
not merely a buffer of recent events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .receptors import Receptor


@dataclass
class FieldPressure:
    """One named pressure with a bounded, decaying value in [0, 1]."""

    name: str
    value: float = 0.0

    def accumulate(self, amount: float, *, decay: float = 0.2) -> None:
        self.value = max(0.0, min(1.0, self.value * (1 - decay) + amount))

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value}


@dataclass
class FieldContinuity:
    """Tracks how continuous the field has been across ticks."""

    tick_count: int = 0
    stable_ticks: int = 0
    last_dominant_modality: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoryFieldState:
    """A serialisable snapshot of the field at one tick."""

    tick: int
    active_modalities: List[str]
    active_receptors: int
    field_pressure: float
    noise_pressure: float
    absence_pressure: float
    novelty_pressure: float
    rhythm_pressure: float
    cross_modal_pressure: float
    uncertainty_pressure: float
    saturation: float
    fatigue: float
    stability: float
    dominant_modality: Optional[str]
    neglected_modality: Optional[str]
    field_tensions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoryField:
    """The continuous, persistent organismic perceptual field."""

    tick: int = 0
    continuity: FieldContinuity = field(default_factory=FieldContinuity)
    pressures: Dict[str, FieldPressure] = field(default_factory=dict)
    active_modalities: Dict[str, int] = field(default_factory=dict)
    dominant_modality: Optional[str] = None
    neglected_modality: Optional[str] = None
    field_tensions: List[str] = field(default_factory=list)
    saturation: float = 0.0
    fatigue: float = 0.0
    stability: float = 1.0

    _PRESSURES = ("field", "noise", "absence", "novelty", "rhythm",
                  "cross_modal", "uncertainty")

    def __post_init__(self) -> None:
        for name in self._PRESSURES:
            self.pressures.setdefault(name, FieldPressure(name))

    def _p(self, name: str) -> FieldPressure:
        return self.pressures.setdefault(name, FieldPressure(name))

    def update(self, receptors: List[Receptor], *,
               novelty: float = 0.0, absence: float = 0.0,
               rhythm: float = 0.0, cross_modal: float = 0.0,
               noise: float = 0.0, tensions: Optional[List[str]] = None,
               ) -> SensoryFieldState:
        """Advance the field one tick from the current receptor population."""
        self.tick += 1
        self.continuity.tick_count += 1

        active = [r for r in receptors if r.event_count > 0]
        # Modality activity counts (how busy each modality has been).
        counts: Dict[str, int] = {}
        intensities: Dict[str, float] = {}
        for r in active:
            counts[r.modality] = counts.get(r.modality, 0) + 1
            intensities[r.modality] = intensities.get(r.modality, 0.0) \
                + r.recent_intensity
        self.active_modalities = counts

        field_amount = (sum(r.recent_intensity for r in active)
                        / max(1, len(active))) if active else 0.0
        self._p("field").accumulate(min(1.0, field_amount))
        self._p("novelty").accumulate(novelty)
        self._p("absence").accumulate(absence)
        self._p("rhythm").accumulate(rhythm)
        self._p("cross_modal").accumulate(cross_modal)
        self._p("noise").accumulate(noise)
        # Uncertainty rises with low reliability and high novelty.
        unreliability = (1.0 - (sum(r.reliability for r in active)
                                / max(1, len(active)))) if active else 0.0
        self._p("uncertainty").accumulate(
            min(1.0, 0.5 * unreliability + 0.5 * novelty))

        self.saturation = (max((r.saturation for r in active), default=0.0))
        self.fatigue = (max((r.fatigue for r in active), default=0.0))

        # Dominant = most intense modality; neglected = least active modality.
        if intensities:
            self.dominant_modality = max(intensities, key=intensities.get)
        if counts:
            self.neglected_modality = min(counts, key=counts.get)

        # Stability: high when novelty/absence/noise pressures are low.
        disturbance = (self._p("novelty").value + self._p("absence").value
                       + self._p("noise").value) / 3.0
        self.stability = max(0.0, 1.0 - disturbance)
        if self.stability > 0.6:
            self.continuity.stable_ticks += 1
        self.continuity.last_dominant_modality = self.dominant_modality

        self.field_tensions = list(tensions or [])
        return self.state(active_receptor_count=len(active))

    def state(self, active_receptor_count: int = 0) -> SensoryFieldState:
        return SensoryFieldState(
            tick=self.tick,
            active_modalities=sorted(self.active_modalities),
            active_receptors=active_receptor_count,
            field_pressure=self._p("field").value,
            noise_pressure=self._p("noise").value,
            absence_pressure=self._p("absence").value,
            novelty_pressure=self._p("novelty").value,
            rhythm_pressure=self._p("rhythm").value,
            cross_modal_pressure=self._p("cross_modal").value,
            uncertainty_pressure=self._p("uncertainty").value,
            saturation=self.saturation,
            fatigue=self.fatigue,
            stability=self.stability,
            dominant_modality=self.dominant_modality,
            neglected_modality=self.neglected_modality,
            field_tensions=list(self.field_tensions))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "continuity": self.continuity.to_dict(),
            "pressures": {n: p.value for n, p in self.pressures.items()},
            "active_modalities": dict(self.active_modalities),
            "dominant_modality": self.dominant_modality,
            "neglected_modality": self.neglected_modality,
            "saturation": self.saturation,
            "fatigue": self.fatigue,
            "stability": self.stability,
            "field_tensions": list(self.field_tensions),
        }
