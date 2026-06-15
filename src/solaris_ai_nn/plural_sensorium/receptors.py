"""Receptors -- the organ-like structures that make a sensorium *stateful*.

A :class:`Receptor` corresponds to one modality/source. It is stateful and
adapts over time: it habituates to the familiar, sensitises to the novel,
fatigues under sustained intensity, and goes silent when its source stops.
Receptor adaptation changes only internal attention/sampling priority -- it never
controls the external feeder or any hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .event_envelope import SensoryEventEnvelope


def event_intensity(envelope: SensoryEventEnvelope) -> float:
    """A modality-agnostic scalar intensity from an envelope's features."""
    values = []
    for value in envelope.features.values():
        if isinstance(value, bool):
            values.append(1.0 if value else 0.0)
        elif isinstance(value, (int, float)):
            values.append(abs(float(value)))
    if not values:
        return 0.0
    return sum(values) / len(values)


class ReceptorAdaptation:
    NORMAL = "normal"
    SENSITIZING = "sensitizing"
    HABITUATING = "habituating"
    FATIGUED = "fatigued"
    SATURATED = "saturated"
    RECOVERING = "recovering"

    ALL = (NORMAL, SENSITIZING, HABITUATING, FATIGUED, SATURATED, RECOVERING)


@dataclass
class ReceptorSensitivity:
    """A bounded sensitivity gain that adapts up (novelty) and down (habit)."""

    value: float = 0.5
    floor: float = 0.05
    ceiling: float = 1.0

    def sensitize(self, amount: float = 0.1) -> None:
        self.value = min(self.ceiling, self.value + amount)

    def habituate(self, amount: float = 0.05) -> None:
        self.value = max(self.floor, self.value - amount)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ReceptorState:
    """A point-in-time snapshot of a receptor's internal variables."""

    intensity: float = 0.0
    novelty: float = 0.0
    fatigue: float = 0.0
    saturation: float = 0.0
    silence_duration: float = 0.0
    reliability: float = 1.0
    adaptation_state: str = ReceptorAdaptation.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Receptor:
    """A stateful, adapting receptor for one modality/source."""

    receptor_id: str
    modality: str
    source_id: str
    sensitivity: ReceptorSensitivity = field(default_factory=ReceptorSensitivity)
    baseline: float = 0.0
    recent_intensity: float = 0.0
    recent_novelty: float = 0.0
    expected_rhythm: Optional[float] = None
    fatigue: float = 0.0
    saturation: float = 0.0
    silence_duration: float = 0.0
    reliability: float = 1.0
    last_event_time: Optional[float] = None
    adaptation_state: str = ReceptorAdaptation.NORMAL
    event_count: int = 0
    adaptation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    _ema: float = field(default=0.0, init=False)
    _ema_n: int = field(default=0, init=False)

    def observe(self, envelope: SensoryEventEnvelope) -> ReceptorState:
        """Update the receptor from a new event and return its new state."""
        intensity = event_intensity(envelope)
        self.event_count += 1
        # Baseline as a slow exponential moving average (never overwritten fast).
        self._ema_n += 1
        alpha = 0.15 if self._ema_n > 1 else 1.0
        self._ema = (1 - alpha) * self._ema + alpha * intensity
        self.baseline = self._ema
        # Novelty: deviation of this event from the slow baseline.
        denom = abs(self.baseline) + 1e-6
        novelty = min(1.0, abs(intensity - self.baseline) / denom)
        self.recent_intensity = intensity
        self.recent_novelty = novelty
        # Fatigue accumulates under sustained high intensity, recovers when low.
        high = intensity > self.baseline * 1.3 + 1e-6
        self.fatigue = min(1.0, self.fatigue + 0.1) if high \
            else max(0.0, self.fatigue - 0.05)
        self.saturation = min(1.0, self.saturation + 0.15) if high \
            else max(0.0, self.saturation - 0.1)
        self.silence_duration = 0.0
        self.last_event_time = envelope.timestamp
        # Reliability drops for untrusted/contaminated sources.
        if envelope.contamination_flags:
            self.reliability = max(0.2, self.reliability - 0.02)
        self._adapt(novelty)
        return self.state()

    def observe_silence(self, elapsed: float = 1.0) -> ReceptorState:
        """No event arrived this tick: accumulate silence, decay fatigue."""
        self.silence_duration += elapsed
        self.fatigue = max(0.0, self.fatigue - 0.05)
        self.saturation = max(0.0, self.saturation - 0.05)
        if self.adaptation_state in (ReceptorAdaptation.FATIGUED,
                                     ReceptorAdaptation.SATURATED):
            self._set_adaptation(ReceptorAdaptation.RECOVERING)
        return self.state()

    def _adapt(self, novelty: float) -> None:
        prev = self.adaptation_state
        if self.saturation >= 0.8:
            self.sensitivity.habituate(0.08)
            self._set_adaptation(ReceptorAdaptation.SATURATED)
        elif self.fatigue >= 0.7:
            self.sensitivity.habituate(0.05)
            self._set_adaptation(ReceptorAdaptation.FATIGUED)
        elif novelty >= 0.5:
            self.sensitivity.sensitize(0.1)
            self._set_adaptation(ReceptorAdaptation.SENSITIZING)
        elif novelty <= 0.1 and self.event_count > 3:
            self.sensitivity.habituate(0.04)
            self._set_adaptation(ReceptorAdaptation.HABITUATING)
        else:
            self._set_adaptation(ReceptorAdaptation.NORMAL)
        if self.adaptation_state != prev:
            self.adaptation_count += 1

    def _set_adaptation(self, state: str) -> None:
        self.adaptation_state = state

    def rest(self) -> None:
        """Internal attention may rest a saturated receptor (no hardware)."""
        self.fatigue = max(0.0, self.fatigue - 0.3)
        self.saturation = max(0.0, self.saturation - 0.3)
        self._set_adaptation(ReceptorAdaptation.RECOVERING)

    def state(self) -> ReceptorState:
        return ReceptorState(
            intensity=self.recent_intensity, novelty=self.recent_novelty,
            fatigue=self.fatigue, saturation=self.saturation,
            silence_duration=self.silence_duration, reliability=self.reliability,
            adaptation_state=self.adaptation_state)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receptor_id": self.receptor_id,
            "modality": self.modality,
            "source_id": self.source_id,
            "sensitivity": self.sensitivity.to_dict(),
            "baseline": self.baseline,
            "recent_intensity": self.recent_intensity,
            "recent_novelty": self.recent_novelty,
            "expected_rhythm": self.expected_rhythm,
            "fatigue": self.fatigue,
            "saturation": self.saturation,
            "silence_duration": self.silence_duration,
            "reliability": self.reliability,
            "last_event_time": self.last_event_time,
            "adaptation_state": self.adaptation_state,
            "event_count": self.event_count,
            "adaptation_count": self.adaptation_count,
            "metadata": dict(self.metadata),
        }
