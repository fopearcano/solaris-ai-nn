"""Adaptive attention -- internal sampling priority, never hardware control.

A :class:`SensoriumAttentionPolicy` decides which modalities to focus, which to
damp, when to wait for an expected signal, and when to rest a saturated receptor.
Every :class:`AttentionShift` changes only *internal* sampling/processing
priority within bounds. Attention cannot control hardware, start external
sensors, or modify source files.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .receptors import Receptor
from .sensory_field import SensoryFieldState


class AttentionAction:
    FOCUS_MODALITY = "focus_modality"
    REDUCE_NOISY_MODALITY = "reduce_noisy_modality"
    INCREASE_POLL_PRIORITY = "increase_internal_polling_priority"
    WAIT_FOR_EXPECTED_SIGNAL = "wait_for_expected_signal"
    COMPARE_MODALITIES = "compare_modalities"
    INSPECT_ABSENCE_WINDOW = "inspect_absence_window"
    MARK_SOURCE_UNRELIABLE = "mark_source_unreliable"
    RECOVER_NEGLECTED_MODALITY = "recover_neglected_modality"
    REST_SATURATED_RECEPTOR = "rest_saturated_receptor"

    ALL = (FOCUS_MODALITY, REDUCE_NOISY_MODALITY, INCREASE_POLL_PRIORITY,
           WAIT_FOR_EXPECTED_SIGNAL, COMPARE_MODALITIES, INSPECT_ABSENCE_WINDOW,
           MARK_SOURCE_UNRELIABLE, RECOVER_NEGLECTED_MODALITY,
           REST_SATURATED_RECEPTOR)


@dataclass
class AttentionShift:
    action: str
    target: str
    reason: str
    priority: float = 0.5
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoriumAttentionState:
    """The current internal-only attention weighting over modalities."""

    focus_modality: Optional[str] = None
    damped_modalities: List[str] = field(default_factory=list)
    modality_priority: Dict[str, float] = field(default_factory=dict)
    waiting_for: Optional[str] = None
    shifts: int = 0
    # A hard guarantee: attention is internal-only.
    controls_hardware: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "focus_modality": self.focus_modality,
            "damped_modalities": list(self.damped_modalities),
            "modality_priority": dict(self.modality_priority),
            "waiting_for": self.waiting_for,
            "shifts": self.shifts,
            "controls_hardware": False,
        }


@dataclass
class SensoriumAttentionPolicy:
    """Chooses bounded internal attention shifts from the field + receptors."""

    max_shifts_per_tick: int = 3
    state: SensoriumAttentionState = field(
        default_factory=SensoriumAttentionState)
    history: List[AttentionShift] = field(default_factory=list)

    def decide(self, field_state: SensoryFieldState,
               receptors: List[Receptor]) -> List[AttentionShift]:
        shifts: List[AttentionShift] = []

        def add(action: str, target: str, reason: str,
                priority: float = 0.5) -> None:
            if len(shifts) >= self.max_shifts_per_tick:
                return
            shift = AttentionShift(action=action, target=target, reason=reason,
                                   priority=priority)
            shifts.append(shift)
            self.history.append(shift)
            self.state.shifts += 1

        # Focus the dominant / novel modality.
        if field_state.novelty_pressure >= 0.5 and field_state.dominant_modality:
            add(AttentionAction.FOCUS_MODALITY, field_state.dominant_modality,
                "high novelty pressure", field_state.novelty_pressure)
            self.state.focus_modality = field_state.dominant_modality
            self.state.modality_priority[field_state.dominant_modality] = 1.0

        # Damp a noisy modality.
        if field_state.noise_pressure >= 0.5 and field_state.dominant_modality:
            target = field_state.dominant_modality
            add(AttentionAction.REDUCE_NOISY_MODALITY, target,
                "high noise pressure", field_state.noise_pressure)
            if target not in self.state.damped_modalities:
                self.state.damped_modalities.append(target)
            self.state.modality_priority[target] = 0.2

        # Inspect an absence window.
        if field_state.absence_pressure >= 0.4:
            add(AttentionAction.INSPECT_ABSENCE_WINDOW, "absence",
                "expected signal may be missing", field_state.absence_pressure)
            self.state.waiting_for = "expected_signal"

        # Recover a neglected modality.
        if field_state.neglected_modality:
            add(AttentionAction.RECOVER_NEGLECTED_MODALITY,
                field_state.neglected_modality, "modality has been neglected",
                0.3)

        # Rest saturated / fatigued receptors and mark unreliable ones.
        for r in receptors:
            if r.saturation >= 0.8 or r.fatigue >= 0.8:
                add(AttentionAction.REST_SATURATED_RECEPTOR, r.receptor_id,
                    "receptor saturated/fatigued", 0.6)
                r.rest()
            elif r.reliability < 0.4:
                add(AttentionAction.MARK_SOURCE_UNRELIABLE, r.source_id,
                    "reliability degraded", 0.5)
        return shifts

    def focus(self, modality: str) -> AttentionShift:
        """Explicitly focus a modality (internal priority only)."""
        self.state.focus_modality = modality
        self.state.modality_priority[modality] = 1.0
        shift = AttentionShift(AttentionAction.FOCUS_MODALITY, modality,
                               "explicit focus", 1.0)
        self.history.append(shift)
        self.state.shifts += 1
        return shift

    def snapshot(self) -> Dict[str, Any]:
        return {"shift_count": self.state.shifts,
                "state": self.state.to_dict(),
                "controls_hardware": False}
