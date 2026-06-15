"""Sensory deprivation -- silence is stimulus, not nothing.

A :class:`DeprivationDetector` detects when sources go silent, a modality is
absent too long, an expected rhythm is missing, or there has been no novelty for a
long interval, and emits :class:`DeprivationEvent`s. Its responses raise absence
pressure, shift attention to the silent source, preserve silence as a stimulus,
create Mysterium pressure, seed an absence hypothesis, and flag a likely-broken
source. Absence can become world-model structure.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class DeprivationKind:
    ALL_SOURCES_SILENT = "all_sources_silent"
    MODALITY_ABSENT_TOO_LONG = "modality_absent_too_long"
    EXPECTED_RHYTHM_MISSING = "expected_rhythm_missing"
    CROSS_MODAL_RELATION_MISSING = "cross_modal_relation_missing"
    NO_NOVELTY_LONG = "no_novelty_for_long_interval"
    NO_STABLE_PATTERN_LONG = "no_stable_pattern_for_long_interval"
    NO_USABLE_SOURCE_HEALTH = "no_usable_source_health"
    SENSORY_STARVATION = "empty_field_sensory_starvation"

    ALL = (ALL_SOURCES_SILENT, MODALITY_ABSENT_TOO_LONG,
           EXPECTED_RHYTHM_MISSING, CROSS_MODAL_RELATION_MISSING,
           NO_NOVELTY_LONG, NO_STABLE_PATTERN_LONG, NO_USABLE_SOURCE_HEALTH,
           SENSORY_STARVATION)


class DeprivationResponse:
    INCREASE_ABSENCE_PRESSURE = "increase_absence_pressure"
    SHIFT_ATTENTION_TO_SILENT_SOURCE = "shift_attention_to_silent_source"
    PRESERVE_SILENCE_AS_STIMULUS = "preserve_silence_as_stimulus"
    CREATE_MYSTERIUM_PRESSURE = "create_mysterium_pressure"
    SEED_ABSENCE_HYPOTHESIS = "seed_hypothesis_about_source_absence"
    TRIGGER_QUIET_CONSOLIDATION = "trigger_quiet_or_consolidation"
    OPERATOR_WARNING_BROKEN_SOURCE = "flag_operator_warning_source_likely_broken"


@dataclass
class DeprivationEvent:
    kind: str
    magnitude: float
    responses: List[str] = field(default_factory=list)
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoryDeprivationState:
    deprived: bool = False
    events: List[DeprivationEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"deprived": self.deprived, "event_count": len(self.events),
                "events": [e.to_dict() for e in self.events],
                "note": "silence is stimulus; absence can become world-model "
                        "structure"}


@dataclass
class DeprivationDetector:
    """Detects deprivation and treats silence/absence as first-class signals."""

    state: SensoryDeprivationState = field(
        default_factory=SensoryDeprivationState)

    def detect(self, *, sensorium: Any = None, source_health: Any = None,
               ) -> List[DeprivationEvent]:
        out: List[DeprivationEvent] = []

        def emit(kind: str, magnitude: float, responses: List[str],
                 detail: str) -> None:
            ev = DeprivationEvent(kind=kind, magnitude=round(magnitude, 4),
                                  responses=responses, detail=detail)
            out.append(ev)
            self.state.events.append(ev)

        if sensorium is not None:
            receptors = list(getattr(sensorium, "receptors", {}).values())
            active = [r for r in receptors
                      if getattr(r, "event_count", 0) > 0]
            field_state = sensorium.sensory_field.state() \
                if hasattr(sensorium, "sensory_field") else None
            if not active:
                emit(DeprivationKind.SENSORY_STARVATION, 1.0,
                     [DeprivationResponse.INCREASE_ABSENCE_PRESSURE,
                      DeprivationResponse.PRESERVE_SILENCE_AS_STIMULUS,
                      DeprivationResponse.CREATE_MYSTERIUM_PRESSURE],
                     "no active receptors; empty field")
            # No novelty for a while -> deprivation of novelty.
            if field_state is not None and \
                    getattr(field_state, "novelty_pressure", 0.0) < 0.05 \
                    and active:
                emit(DeprivationKind.NO_NOVELTY_LONG, 1.0,
                     [DeprivationResponse.SEED_ABSENCE_HYPOTHESIS],
                     "novelty pressure near zero")
            # Silent receptors (long silence) -> modality absent.
            for r in receptors:
                if getattr(r, "silence_duration", 0.0) >= 3.0:
                    emit(DeprivationKind.MODALITY_ABSENT_TOO_LONG,
                         min(1.0, getattr(r, "silence_duration", 0.0) / 10.0),
                         [DeprivationResponse.SHIFT_ATTENTION_TO_SILENT_SOURCE,
                          DeprivationResponse.PRESERVE_SILENCE_AS_STIMULUS],
                         f"{getattr(r, 'modality', '?')} silent")

        if source_health is not None:
            silent = getattr(source_health, "silent_sources", lambda: [])()
            active_s = getattr(source_health, "active_sources", lambda: [])()
            if silent and not active_s:
                emit(DeprivationKind.ALL_SOURCES_SILENT, 1.0,
                     [DeprivationResponse.INCREASE_ABSENCE_PRESSURE,
                      DeprivationResponse.OPERATOR_WARNING_BROKEN_SOURCE,
                      DeprivationResponse.TRIGGER_QUIET_CONSOLIDATION],
                     "all known sources silent")

        self.state.deprived = bool(self.state.events)
        return out
