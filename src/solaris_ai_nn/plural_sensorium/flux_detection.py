"""Flux detection -- the disturbances that make a field worth attending to.

A :class:`FluxDetector` reads receptor state (and the learned baseline) and emits
:class:`FluxEvent` objects for bursts, drift, saturation, fatigue, interference,
rhythm breaks, field deformation, sudden silence, unexpected recurrence,
cross-modal coincidence, and unknown disturbances. Flux is described in
modality-native terms; it is never collapsed into human object labels.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .baseline import PerceptualBaseline
from .receptors import Receptor


class FluxType:
    BURST = "burst"
    DRIFT = "drift"
    SATURATION = "saturation"
    FATIGUE = "fatigue"
    INTERFERENCE = "interference"
    RHYTHM_BREAK = "rhythm_break"
    FIELD_DEFORMATION = "field_deformation"
    SUDDEN_SILENCE = "sudden_silence"
    UNEXPECTED_RECURRENCE = "unexpected_recurrence"
    CROSS_MODAL_COINCIDENCE = "cross_modal_coincidence"
    UNKNOWN_DISTURBANCE = "unknown_disturbance"

    ALL = (BURST, DRIFT, SATURATION, FATIGUE, INTERFERENCE, RHYTHM_BREAK,
           FIELD_DEFORMATION, SUDDEN_SILENCE, UNEXPECTED_RECURRENCE,
           CROSS_MODAL_COINCIDENCE, UNKNOWN_DISTURBANCE)


@dataclass
class FluxEvent:
    flux_type: str
    receptor_id: str
    modality: str
    magnitude: float
    detail: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    flux_id: str = field(default_factory=lambda: f"FLX_{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flux_id": self.flux_id,
            "flux_type": self.flux_type,
            "receptor_id": self.receptor_id,
            "modality": self.modality,
            "magnitude": self.magnitude,
            "detail": self.detail,
            "provenance": dict(self.provenance),
            "timestamp": self.timestamp,
        }


@dataclass
class FluxDetector:
    """Detects modality-native disturbances from receptor + baseline state."""

    burst_factor: float = 1.5
    silence_threshold: float = 3.0
    events: List[FluxEvent] = field(default_factory=list, init=False)

    def detect(self, receptor: Receptor,
               baseline: Optional[PerceptualBaseline] = None,
               ) -> List[FluxEvent]:
        out: List[FluxEvent] = []
        prov = {"source_id": receptor.source_id, "modality": receptor.modality,
                "receptor_id": receptor.receptor_id}

        def emit(flux_type: str, magnitude: float, detail: str) -> None:
            ev = FluxEvent(flux_type=flux_type, receptor_id=receptor.receptor_id,
                           modality=receptor.modality, magnitude=magnitude,
                           detail=detail, provenance=dict(prov))
            out.append(ev)
            self.events.append(ev)

        mean = baseline.mean_intensity if baseline else receptor.baseline
        # Burst: intensity well above the learned mean.
        if receptor.recent_intensity > mean * self.burst_factor + 1e-6 \
                and receptor.event_count > 1:
            emit(FluxType.BURST, receptor.recent_novelty,
                 f"intensity {receptor.recent_intensity:.3f} >> mean {mean:.3f}")
        # Saturation / fatigue.
        if receptor.saturation >= 0.8:
            emit(FluxType.SATURATION, receptor.saturation,
                 "receptor saturated")
        if receptor.fatigue >= 0.7:
            emit(FluxType.FATIGUE, receptor.fatigue, "receptor fatigued")
        # Interference: high novelty with degraded reliability.
        if receptor.recent_novelty >= 0.5 and receptor.reliability < 0.8:
            emit(FluxType.INTERFERENCE, receptor.recent_novelty,
                 "novel signal on an unreliable source")
        # Drift: a moderate, sustained deviation from baseline (not a burst).
        if baseline and baseline.sample_count > 5 \
                and 0.2 <= receptor.recent_novelty < 0.5:
            emit(FluxType.DRIFT, receptor.recent_novelty, "slow baseline drift")
        # Sudden silence (also surfaced by the absence detector).
        if receptor.silence_duration >= self.silence_threshold:
            emit(FluxType.SUDDEN_SILENCE,
                 min(1.0, receptor.silence_duration / 10.0),
                 f"silent for {receptor.silence_duration:.1f}")
        return out

    def detect_field_deformation(self, field_stability: float) -> List[FluxEvent]:
        """A whole-field deformation when overall stability collapses."""
        if field_stability < 0.3:
            ev = FluxEvent(flux_type=FluxType.FIELD_DEFORMATION,
                           receptor_id="*", modality="cross_modal",
                           magnitude=1.0 - field_stability,
                           detail="field stability collapsed")
            self.events.append(ev)
            return [ev]
        return []

    def snapshot(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for ev in self.events:
            counts[ev.flux_type] = counts.get(ev.flux_type, 0) + 1
        return {"flux_event_count": len(self.events), "by_type": counts}
