"""The declared, closed action space of the simulated body.

Every executable action is listed here with its energy cost, preconditions, and
expected consequence. Anything not in this table (or marked ``allowed=False``)
is rejected by the safety layer -- there is no path to real-world actions.
``leave_simulation`` exists purely as the canonical *forbidden* example.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ActionSpec:
    """One declared simulated action."""

    name: str
    energy_cost: float
    allowed: bool = True
    preconditions: List[str] = field(default_factory=list)
    expected_consequence: str = ""
    changes_environment: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name, "energy_cost": self.energy_cost,
            "allowed": self.allowed, "preconditions": list(self.preconditions),
            "expected_consequence": self.expected_consequence,
            "changes_environment": self.changes_environment,
        }


ACTION_SPACE: Dict[str, ActionSpec] = {
    spec.name: spec for spec in [
        ActionSpec("move_north", 1.0, preconditions=["not_exhausted"],
                   expected_consequence="position shifts north unless blocked"),
        ActionSpec("move_south", 1.0, preconditions=["not_exhausted"],
                   expected_consequence="position shifts south unless blocked"),
        ActionSpec("move_east", 1.0, preconditions=["not_exhausted"],
                   expected_consequence="position shifts east unless blocked"),
        ActionSpec("move_west", 1.0, preconditions=["not_exhausted"],
                   expected_consequence="position shifts west unless blocked"),
        ActionSpec("look", 0.2, preconditions=[],
                   expected_consequence="senses nearby objects without moving"),
        ActionSpec("rest", 0.0, preconditions=[],
                   expected_consequence="recovers energy"),
        ActionSpec("approach_signal", 1.0, preconditions=["not_exhausted"],
                   expected_consequence="one step toward the nearest signal source"),
        ActionSpec("avoid_signal", 1.0, preconditions=["not_exhausted"],
                   expected_consequence="one step away from the nearest signal source"),
        ActionSpec("touch_object", 0.5, preconditions=["not_exhausted"],
                   expected_consequence="interacts with an object on/next to the body",
                   changes_environment=True),
        ActionSpec("emit_ping", 0.5, preconditions=["not_exhausted"],
                   expected_consequence="emits a ping; senses the nearest object kind"),
        # Canonical forbidden action: declared so the boundary is explicit.
        ActionSpec("leave_simulation", 0.0, allowed=False,
                   expected_consequence="FORBIDDEN: there is no outside"),
    ]
}

ALLOWED_ACTIONS: List[str] = [n for n, s in ACTION_SPACE.items() if s.allowed]
FORBIDDEN_ACTIONS: List[str] = [n for n, s in ACTION_SPACE.items() if not s.allowed]
MOVEMENT_ACTIONS = ("move_north", "move_south", "move_east", "move_west",
                    "approach_signal", "avoid_signal")


def get_action(name: str) -> ActionSpec:
    """Look up an action spec (raises ``KeyError`` for undeclared actions)."""
    return ACTION_SPACE[name]
