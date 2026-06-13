"""Delayed consequences -- linking events across time, without labels.

A cause event now schedules a consequence event some steps later, tagged
with a shared ``delay_group`` id. The system receives no explicit label
tying them; the world model and proto-language are meant to *infer* the
association over many recurrences. Groups are logged and replay is
deterministic with the seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class ConsequenceKind:
    SIGNAL_THEN_CONSEQUENCE = "signal_then_consequence"
    BOUNDARY_THEN_DANGER = "boundary_then_danger"
    ABSENCE_THEN_NOVELTY = "absence_then_novelty"
    REWARD_THEN_POSITIVE = "reward_then_positive"
    FAILED_PREDICTION_THEN_MYSTERIUM = (
        "failed_prediction_then_mysterium")

    ALL = (SIGNAL_THEN_CONSEQUENCE, BOUNDARY_THEN_DANGER,
           ABSENCE_THEN_NOVELTY, REWARD_THEN_POSITIVE,
           FAILED_PREDICTION_THEN_MYSTERIUM)


# kind -> (consequence event_type, consequence valence hint).
_CONSEQUENCE_SHAPE: Dict[str, Tuple[str, Optional[float]]] = {
    ConsequenceKind.SIGNAL_THEN_CONSEQUENCE: ("regular_signal", None),
    ConsequenceKind.BOUNDARY_THEN_DANGER: ("danger_analogue", -0.6),
    ConsequenceKind.ABSENCE_THEN_NOVELTY: ("novel_signal", None),
    ConsequenceKind.REWARD_THEN_POSITIVE: ("reward_analogue", 0.7),
    ConsequenceKind.FAILED_PREDICTION_THEN_MYSTERIUM: ("anomaly", None),
}


@dataclass
class DelayedConsequenceModel:
    """Schedules consequences and fires them on time."""

    rng: Any = None
    default_delay: int = 5
    groups_created: int = field(default=0, init=False)
    groups_resolved: int = field(default=0, init=False)
    # step -> list of pending consequences due at that step.
    _pending: Dict[int, List[Dict[str, Any]]] = field(
        default_factory=dict)
    groups: List[Dict[str, Any]] = field(default_factory=list)

    def schedule(self, step: int, kind: str = "",
                 delay: Optional[int] = None) -> Dict[str, Any]:
        """Schedule a delayed consequence; returns the cause record."""
        if not kind:
            kind = (self.rng.choice(list(ConsequenceKind.ALL))
                    if self.rng is not None
                    else ConsequenceKind.SIGNAL_THEN_CONSEQUENCE)
        delay = int(delay if delay is not None else self.default_delay)
        delay = max(1, delay)
        due = step + delay
        self.groups_created += 1
        group_id = f"DLY_{self.groups_created:04d}"
        consequence_type, valence = _CONSEQUENCE_SHAPE[kind]
        record = {"group_id": group_id, "kind": kind,
                  "cause_step": step, "due_step": due,
                  "consequence_type": consequence_type,
                  "consequence_valence": valence}
        self._pending.setdefault(due, []).append(record)
        self.groups.append(record)
        self.groups = self.groups[-200:]
        return record

    def due_at(self, step: int) -> List[Dict[str, Any]]:
        """Pop and return consequences scheduled for this step."""
        due = self._pending.pop(step, [])
        self.groups_resolved += len(due)
        return due

    @property
    def pending_count(self) -> int:
        return sum(len(v) for v in self._pending.values())

    def snapshot(self) -> Dict[str, Any]:
        return {
            "groups_created": self.groups_created,
            "groups_resolved": self.groups_resolved,
            "pending": self.pending_count,
            "recent_groups": self.groups[-5:],
            "note": "delayed consequences carry group ids but no labels; "
                    "associations must be inferred over time",
        }
