"""Sensory overload -- detect when too much is arriving, and throttle internally.

An :class:`OverloadDetector` watches the per-tick event count, modality
saturation, receptor fatigue, noise, and the growth of proto-symbols / hypotheses
/ LOGOS tensions / memory, and emits :class:`OverloadEvent`s with internal
responses (throttle, quarantine a noisy source internally, pause proto-symbol
creation, trigger consolidation, warn the operator). It never deletes raw
evidence, never modifies a source, and never hides overload.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class OverloadKind:
    EVENT_FLOOD = "too_many_events_per_tick"
    MODALITY_SATURATION = "modality_saturation"
    RECEPTOR_FATIGUE = "receptor_fatigue"
    NOISE_STORM = "noise_storm"
    CROSS_MODAL_EXPLOSION = "cross_modal_explosion"
    PROTO_SYMBOL_EXPLOSION = "proto_symbol_candidate_explosion"
    HYPOTHESIS_EXPLOSION = "hypothesis_explosion"
    LOGOS_TENSION_EXPLOSION = "logos_tension_explosion"
    MEMORY_GROWTH_SPIKE = "memory_growth_spike"
    SOURCE_CORRUPTION_FLOOD = "source_corruption_flood"
    ARTIFACT_BLOAT = "report_artifact_bloat"

    ALL = (EVENT_FLOOD, MODALITY_SATURATION, RECEPTOR_FATIGUE, NOISE_STORM,
           CROSS_MODAL_EXPLOSION, PROTO_SYMBOL_EXPLOSION, HYPOTHESIS_EXPLOSION,
           LOGOS_TENSION_EXPLOSION, MEMORY_GROWTH_SPIKE,
           SOURCE_CORRUPTION_FLOOD, ARTIFACT_BLOAT)


class OverloadResponse:
    THROTTLE = "throttle_internal_processing"
    QUARANTINE_NOISY_SOURCE = "quarantine_noisy_source_internally"
    REDUCE_NOVELTY_SENSITIVITY = "reduce_novelty_sensitivity"
    PAUSE_PROTO_SYMBOL_CREATION = "pause_proto_symbol_creation"
    DEFER_HYPOTHESIS_GENERATION = "defer_hypothesis_generation"
    TRIGGER_CONSOLIDATION = "trigger_consolidation"
    AUTOREGENERATION_WARNING = "trigger_auto_regeneration_warning"
    OPERATOR_WARNING = "create_operator_warning"


@dataclass
class OverloadEvent:
    kind: str
    magnitude: float
    responses: List[str] = field(default_factory=list)
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoryOverloadState:
    overloaded: bool = False
    events: List[OverloadEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"overloaded": self.overloaded,
                "event_count": len(self.events),
                "events": [e.to_dict() for e in self.events],
                "note": "overload is reported, never hidden; no evidence is "
                        "deleted and no source is modified"}


@dataclass
class OverloadDetector:
    """Detects overload and recommends internal throttling (never deletes)."""

    events_per_tick_threshold: int = 50
    explosion_threshold: int = 40
    state: SensoryOverloadState = field(default_factory=SensoryOverloadState)

    def detect(self, *, events_this_tick: int = 0, sensorium: Any = None,
               source_health: Any = None) -> List[OverloadEvent]:
        out: List[OverloadEvent] = []

        def emit(kind: str, magnitude: float, responses: List[str],
                 detail: str) -> None:
            ev = OverloadEvent(kind=kind, magnitude=round(magnitude, 4),
                               responses=responses, detail=detail)
            out.append(ev)
            self.state.events.append(ev)

        if events_this_tick >= self.events_per_tick_threshold:
            emit(OverloadKind.EVENT_FLOOD,
                 events_this_tick / self.events_per_tick_threshold,
                 [OverloadResponse.THROTTLE, OverloadResponse.TRIGGER_CONSOLIDATION],
                 f"{events_this_tick} events this tick")

        if sensorium is not None:
            receptors = list(getattr(sensorium, "receptors", {}).values())
            if any(getattr(r, "saturation", 0.0) >= 0.8 for r in receptors):
                emit(OverloadKind.MODALITY_SATURATION, 1.0,
                     [OverloadResponse.REDUCE_NOVELTY_SENSITIVITY],
                     "a modality saturated")
            if any(getattr(r, "fatigue", 0.0) >= 0.7 for r in receptors):
                emit(OverloadKind.RECEPTOR_FATIGUE, 1.0,
                     [OverloadResponse.TRIGGER_CONSOLIDATION],
                     "receptor fatigue high")
            field_state = sensorium.sensory_field.state() \
                if hasattr(sensorium, "sensory_field") else None
            if field_state is not None and \
                    getattr(field_state, "noise_pressure", 0.0) >= 0.6:
                emit(OverloadKind.NOISE_STORM,
                     getattr(field_state, "noise_pressure", 0.0),
                     [OverloadResponse.QUARANTINE_NOISY_SOURCE,
                      OverloadResponse.REDUCE_NOVELTY_SENSITIVITY],
                     "noise storm")
            n_proto = len(getattr(sensorium, "proto_symbol_candidates", []))
            if n_proto >= self.explosion_threshold:
                emit(OverloadKind.PROTO_SYMBOL_EXPLOSION,
                     n_proto / self.explosion_threshold,
                     [OverloadResponse.PAUSE_PROTO_SYMBOL_CREATION,
                      OverloadResponse.TRIGGER_CONSOLIDATION],
                     f"{n_proto} proto-symbol candidates")
            n_hyp = len(getattr(sensorium, "hypotheses", []))
            if n_hyp >= self.explosion_threshold:
                emit(OverloadKind.HYPOTHESIS_EXPLOSION,
                     n_hyp / self.explosion_threshold,
                     [OverloadResponse.DEFER_HYPOTHESIS_GENERATION],
                     f"{n_hyp} hypotheses")
            n_tension = len(getattr(sensorium, "logos_tensions", []))
            if n_tension >= self.explosion_threshold:
                emit(OverloadKind.LOGOS_TENSION_EXPLOSION,
                     n_tension / self.explosion_threshold,
                     [OverloadResponse.TRIGGER_CONSOLIDATION],
                     f"{n_tension} LOGOS tensions")

        if source_health is not None:
            corrupt = getattr(source_health, "corrupt_sources", lambda: [])()
            if len(corrupt) >= 2:
                emit(OverloadKind.SOURCE_CORRUPTION_FLOOD, len(corrupt),
                     [OverloadResponse.AUTOREGENERATION_WARNING,
                      OverloadResponse.OPERATOR_WARNING],
                     f"{len(corrupt)} corrupt sources")

        self.state.overloaded = bool(self.state.events)
        return out
