"""Habit formation -- learned operational policy tendencies, not instincts or will.

A :class:`SensoriumHabit` is a trigger->action tendency that strengthens with
repeated constructive evidence. Habits are operational policy tendencies, NOT
instincts, personality, or will; they remain overrideable by safety/governance,
can be weakened or inhibited, and always preserve their evidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class HabitTrigger:
    SOURCE_SILENCE_REPEATS = "source_silence_repeats"
    SIGN_DRIFT_RISES = "sign_drift_rises"
    OVERLOAD_RISES = "overload_rises"
    PREDICTION_FAILS_REPEATEDLY = "prediction_fails_repeatedly"
    MODALITY_IGNORED_TOO_LONG = "modality_ignored_too_long"
    LABEL_CONTAMINATION_RISES = "label_contamination_rises"
    BOUNDARY_UNCERTAIN = "boundary_uncertain"
    UNKNOWN = "unknown"

    ALL = (SOURCE_SILENCE_REPEATS, SIGN_DRIFT_RISES, OVERLOAD_RISES,
           PREDICTION_FAILS_REPEATEDLY, MODALITY_IGNORED_TOO_LONG,
           LABEL_CONTAMINATION_RISES, BOUNDARY_UNCERTAIN, UNKNOWN)


class HabitStrength:
    CANDIDATE = "candidate"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    WEAKENED = "weakened"
    INHIBITED = "inhibited"

    @staticmethod
    def band(value: float) -> str:
        if value <= 0.0:
            return HabitStrength.INHIBITED
        if value < 0.3:
            return HabitStrength.CANDIDATE
        if value < 0.5:
            return HabitStrength.WEAK
        if value < 0.75:
            return HabitStrength.MODERATE
        return HabitStrength.STRONG


# Trigger -> recommended action kind (the learned tendency).
_TRIGGER_ACTION = {
    HabitTrigger.SOURCE_SILENCE_REPEATS: "inspect_absence_window",
    HabitTrigger.SIGN_DRIFT_RISES: "compare_modalities",
    HabitTrigger.OVERLOAD_RISES: "no_op",
    HabitTrigger.PREDICTION_FAILS_REPEATEDLY: "preserve_unknown",
    HabitTrigger.MODALITY_IGNORED_TOO_LONG: "shift_attention",
    HabitTrigger.LABEL_CONTAMINATION_RISES: "mark_source_unreliable",
    HabitTrigger.BOUNDARY_UNCERTAIN: "no_op",
}


@dataclass
class SensoriumHabit:
    """One learned trigger->action tendency (overrideable; not instinct)."""

    trigger: str
    action_kind: str = ""
    habit_id: str = field(default_factory=lambda: f"HBT_{uuid.uuid4().hex[:8]}")
    strength: float = 0.0
    reinforcement_count: int = 0
    weaken_count: int = 0
    inhibited: bool = False
    evidence_refs: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.action_kind:
            self.action_kind = _TRIGGER_ACTION.get(self.trigger, "no_op")

    @property
    def strength_band(self) -> str:
        if self.inhibited:
            return HabitStrength.INHIBITED
        return HabitStrength.band(self.strength)

    def reinforce(self, amount: float = 0.2) -> None:
        self.strength = round(min(1.0, self.strength + amount), 4)
        self.reinforcement_count += 1

    def weaken(self, amount: float = 0.3) -> None:
        self.strength = round(max(0.0, self.strength - amount), 4)
        self.weaken_count += 1

    def inhibit(self) -> None:
        # Safety/governance can always override a habit.
        self.inhibited = True
        self.strength = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "habit_id": self.habit_id,
            "trigger": self.trigger,
            "action_kind": self.action_kind,
            "strength": round(self.strength, 4),
            "strength_band": self.strength_band,
            "reinforcement_count": self.reinforcement_count,
            "weaken_count": self.weaken_count,
            "inhibited": self.inhibited,
            "evidence_refs": list(self.evidence_refs),
            "note": "learned policy tendency, overrideable by safety/governance; "
                    "not instinct, personality, or will",
        }


@dataclass
class HabitFormationEngine:
    """Forms and adjusts habits from repeated action-reaction evidence."""

    habits: Dict[str, SensoriumHabit] = field(default_factory=dict)

    def _habit(self, trigger: str) -> SensoriumHabit:
        h = self.habits.get(trigger)
        if h is None:
            h = SensoriumHabit(trigger=trigger)
            self.habits[trigger] = h
        return h

    def reinforce(self, trigger: str, *,
                  evidence_ref: str = "") -> SensoriumHabit:
        h = self._habit(trigger)
        h.reinforce()
        if evidence_ref:
            h.evidence_refs.append(evidence_ref)
        return h

    def weaken(self, trigger: str) -> SensoriumHabit:
        h = self._habit(trigger)
        h.weaken()
        return h

    def inhibit(self, trigger: str) -> SensoriumHabit:
        h = self._habit(trigger)
        h.inhibit()
        return h

    def candidates(self) -> List[SensoriumHabit]:
        return [h for h in self.habits.values()
                if not h.inhibited and h.reinforcement_count >= 1]

    def strengthened(self) -> List[SensoriumHabit]:
        return [h for h in self.habits.values() if h.strength >= 0.5]

    def weakened(self) -> List[SensoriumHabit]:
        return [h for h in self.habits.values() if h.weaken_count > 0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "habit_count": len(self.habits),
            "candidate_count": len(self.candidates()),
            "strengthened_count": len(self.strengthened()),
            "weakened_count": len(self.weakened()),
            "habits": [h.to_dict() for h in self.habits.values()],
        }
