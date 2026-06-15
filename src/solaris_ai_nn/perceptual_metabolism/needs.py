"""Perceptual needs -- operational regulatory pressures, never feelings.

A :class:`PerceptualNeed` is an operational pressure that rises and falls with the
sensory field and influences *internal* attention and processing only. Needs are
NOT emotions, NOT feelings, and NOT subjective experience; they cannot produce any
real-world action. The :class:`PerceptualNeedModel` updates the full set of needs
from the current field/receptor state each tick.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PerceptualNeedType:
    NOVELTY = "novelty_need"
    RHYTHM = "rhythm_need"
    STABILITY = "stability_need"
    ABSENCE_RESOLUTION = "absence_resolution_need"
    CROSS_MODAL = "cross_modal_need"
    SOURCE_RELIABILITY = "source_reliability_need"
    QUIET = "quiet_need"
    CONSOLIDATION = "consolidation_need"
    EXPLORATION = "exploration_need"
    RECOVERY = "recovery_need"

    ALL = (NOVELTY, RHYTHM, STABILITY, ABSENCE_RESOLUTION, CROSS_MODAL,
           SOURCE_RELIABILITY, QUIET, CONSOLIDATION, EXPLORATION, RECOVERY)


@dataclass
class PerceptualNeedState:
    pressure: float
    trend: float
    saturated: bool
    deprived: bool

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PerceptualNeed:
    """One operational perceptual pressure (not a feeling)."""

    need_type: str
    pressure: float = 0.0
    baseline_pressure: float = 0.3
    trend: float = 0.0
    saturation_threshold: float = 0.8
    deprivation_threshold: float = 0.15
    decay_rate: float = 0.1
    last_satisfied_tick: int = 0
    source_modalities: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set_pressure(self, value: float, tick: int = 0) -> None:
        value = max(0.0, min(1.0, value))
        self.trend = round(value - self.pressure, 4)
        self.pressure = value
        if value < self.deprivation_threshold:
            self.last_satisfied_tick = tick

    @property
    def saturated(self) -> bool:
        return self.pressure >= self.saturation_threshold

    @property
    def deprived(self) -> bool:
        return self.pressure <= self.deprivation_threshold

    def state(self) -> PerceptualNeedState:
        return PerceptualNeedState(pressure=round(self.pressure, 4),
                                   trend=self.trend, saturated=self.saturated,
                                   deprived=self.deprived)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "need_type": self.need_type,
            "pressure": round(self.pressure, 4),
            "baseline_pressure": self.baseline_pressure,
            "trend": self.trend,
            "saturation_threshold": self.saturation_threshold,
            "deprivation_threshold": self.deprivation_threshold,
            "saturated": self.saturated,
            "deprived": self.deprived,
            "last_satisfied_tick": self.last_satisfied_tick,
            "source_modalities": list(self.source_modalities),
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
            "note": "operational pressure, not a feeling",
        }


@dataclass
class PerceptualNeedModel:
    """Maintains all perceptual needs and updates them from sensory state."""

    needs: Dict[str, PerceptualNeed] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.needs:
            for t in PerceptualNeedType.ALL:
                self.needs[t] = PerceptualNeed(need_type=t)

    def get(self, need_type: str) -> Optional[PerceptualNeed]:
        return self.needs.get(need_type)

    def update(self, field_state: Any, receptors: List[Any], *,
               tick: int = 0) -> None:
        """Recompute need pressures from the current field/receptor state."""
        p = self._pressures(field_state)
        active = [r for r in receptors if getattr(r, "event_count", 0) > 0]
        fatigue = max((getattr(r, "fatigue", 0.0) for r in active), default=0.0)
        saturation = max((getattr(r, "saturation", 0.0) for r in active),
                         default=0.0)
        unreliable = sum(1 for r in active
                         if getattr(r, "reliability", 1.0) < 0.8)
        unreliable_frac = unreliable / max(1, len(active))
        modality_count = len({getattr(r, "modality", "") for r in active})

        N = PerceptualNeedType
        # Novelty need rises when novelty is scarce; falls when it is plentiful.
        self.needs[N.NOVELTY].set_pressure(1.0 - p.get("novelty", 0.0), tick)
        self.needs[N.RHYTHM].set_pressure(1.0 - p.get("rhythm", 0.0), tick)
        self.needs[N.STABILITY].set_pressure(
            max(p.get("noise", 0.0), p.get("novelty", 0.0)), tick)
        self.needs[N.ABSENCE_RESOLUTION].set_pressure(p.get("absence", 0.0),
                                                      tick)
        self.needs[N.CROSS_MODAL].set_pressure(
            1.0 - p.get("cross_modal", 0.0) if modality_count > 1 else 0.0, tick)
        self.needs[N.SOURCE_RELIABILITY].set_pressure(unreliable_frac, tick)
        self.needs[N.QUIET].set_pressure(
            max(p.get("field", 0.0), saturation), tick)
        self.needs[N.CONSOLIDATION].set_pressure(
            min(1.0, 0.5 * fatigue + 0.5 * saturation), tick)
        self.needs[N.EXPLORATION].set_pressure(
            1.0 - min(1.0, modality_count / 4.0), tick)
        self.needs[N.RECOVERY].set_pressure(fatigue, tick)

        for need in self.needs.values():
            need.source_modalities = sorted(
                {getattr(r, "modality", "") for r in active})

    @staticmethod
    def _pressures(field_state: Any) -> Dict[str, float]:
        if field_state is None:
            return {}
        if isinstance(field_state, dict):
            return {k: float(v) for k, v in field_state.items()
                    if isinstance(v, (int, float))}
        return {
            "field": getattr(field_state, "field_pressure", 0.0),
            "noise": getattr(field_state, "noise_pressure", 0.0),
            "absence": getattr(field_state, "absence_pressure", 0.0),
            "novelty": getattr(field_state, "novelty_pressure", 0.0),
            "rhythm": getattr(field_state, "rhythm_pressure", 0.0),
            "cross_modal": getattr(field_state, "cross_modal_pressure", 0.0),
        }

    def dominant(self) -> Optional[PerceptualNeed]:
        if not self.needs:
            return None
        return max(self.needs.values(), key=lambda n: n.pressure)

    def to_dict(self) -> Dict[str, Any]:
        dominant = self.dominant()
        return {
            "need_count": len(self.needs),
            "dominant_need": dominant.need_type if dominant else None,
            "dominant_pressure": round(dominant.pressure, 4) if dominant else 0.0,
            "needs": {t: n.to_dict() for t, n in self.needs.items()},
            "note": "needs are operational pressures, not feelings or emotions",
        }
