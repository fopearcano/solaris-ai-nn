"""Stimulus ecology primitives -- the events a developmental world emits.

An :class:`EcologyStimulus` is *not* a supervised label. Human-readable
fields (``payload``, ``metadata``) are provenance for inspection only; the
developing system is expected to infer structure from recurrence,
consequence, and context -- never from an answer key. Every event carries
its source so the ego layer can attribute it as nursery-generated and
never as an operator command or a real-world event.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class EcologyEventType:
    REGULAR_SIGNAL = "regular_signal"
    ABSENCE_WINDOW = "absence_window"
    NOVEL_SIGNAL = "novel_signal"
    REPEATED_PATTERN = "repeated_pattern"
    PATTERN_BREAK = "pattern_break"
    SCARCITY_EVENT = "scarcity_event"
    REWARD_ANALOGUE = "reward_analogue"
    DANGER_ANALOGUE = "danger_analogue"
    BOUNDARY_EVENT = "boundary_event"
    DELAYED_CONSEQUENCE = "delayed_consequence"
    SEASONAL_SHIFT = "seasonal_shift"
    NOISE_BURST = "noise_burst"
    QUIET_PHASE = "quiet_phase"
    RECOVERY_PHASE = "recovery_phase"
    RARE_EVENT = "rare_event"
    ANOMALY = "anomaly"
    MILESTONE_TRIGGER = "milestone_trigger"

    ALL = (REGULAR_SIGNAL, ABSENCE_WINDOW, NOVEL_SIGNAL, REPEATED_PATTERN,
           PATTERN_BREAK, SCARCITY_EVENT, REWARD_ANALOGUE,
           DANGER_ANALOGUE, BOUNDARY_EVENT, DELAYED_CONSEQUENCE,
           SEASONAL_SHIFT, NOISE_BURST, QUIET_PHASE, RECOVERY_PHASE,
           RARE_EVENT, ANOMALY, MILESTONE_TRIGGER)

    # Event types that carry no external signal (silence-like).
    ABSENCE_LIKE = frozenset({ABSENCE_WINDOW, QUIET_PHASE, SCARCITY_EVENT})


class StimulusSource:
    DEVELOPMENTAL_NURSERY = "developmental_nursery"
    SIMULATED_ENVIRONMENT = "simulated_environment"
    READ_ONLY_STREAM = "read_only_stream"

    ALL = (DEVELOPMENTAL_NURSERY, SIMULATED_ENVIRONMENT,
           READ_ONLY_STREAM)


ECOLOGY_NOTE = ("an artificial developmental stimulus, not a supervised "
                "label, an operator command, or a real-world event")


@dataclass
class EcologyStimulus:
    """One stimulus from the developmental ecology."""

    event_type: str
    source: str = StimulusSource.DEVELOPMENTAL_NURSERY
    modality: str = "generic"
    payload: Any = None
    intensity: float = 0.0  # [0, 1]
    stimulus_id: str = ""
    step: int = 0
    timestamp: float = field(default_factory=time.time)
    valence_hint: Optional[float] = None     # [-1, 1] provenance only
    novelty_hint: Optional[float] = None      # [0, 1] provenance only
    expected_pattern_id: Optional[str] = None
    delay_group: Optional[str] = None
    recurrence_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event_type not in EcologyEventType.ALL:
            raise ValueError(f"unknown ecology event type "
                             f"{self.event_type!r}")
        if not self.stimulus_id:
            self.stimulus_id = f"eco_{self.step}_{self.event_type}"
        self.intensity = max(0.0, min(1.0, float(self.intensity)))

    @property
    def is_absence(self) -> bool:
        return self.event_type in EcologyEventType.ABSENCE_LIKE

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_absence": self.is_absence,
                "note": ECOLOGY_NOTE}


@dataclass
class EcologyEvent:
    """A logged ecology happening (a stimulus plus bookkeeping)."""

    stimulus: EcologyStimulus
    regime: str = ""
    cycle_phase: str = ""
    season: str = ""
    step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "regime": self.regime,
            "cycle_phase": self.cycle_phase,
            "season": self.season,
            "stimulus": self.stimulus.to_dict(),
        }
