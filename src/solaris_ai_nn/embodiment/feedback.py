"""EmbodimentFeedback -- consequences become canonical Reaction events.

The world grades what the body just did: approaching reward is good, hitting
obstacles is bad, touching the unknown is mildly rewarding novelty, resting
when depleted is good, and repeating a useless action drifts negative. The
result is a valence in [-1, +1] wrapped as a canonical ``Reaction`` -- the
exact feedback signal the readout/habit machinery already learns from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..signals import canonical as C
from ..utils.math import clamp
from .base import ActionResult


@dataclass
class EmbodimentFeedback:
    """Stateless rules + a tiny repetition memory.

    ``evaluate`` takes the action result plus before/after world summaries
    (distances to reward/danger, energy state) and returns a Reaction or None
    (neutral outcomes produce no feedback).
    """

    useless_repeat_limit: int = 3
    _recent: List[str] = field(default_factory=list)
    useless_repeats: int = 0

    def evaluate(self, result: ActionResult, before: Dict[str, Any],
                 after: Dict[str, Any]) -> Optional[C.Reaction]:
        valence = 0.0
        reasons: List[str] = []

        # Collisions: walls and obstacles hurt.
        if result.blocked_reason in ("wall", "obstacle"):
            valence -= 0.6
            reasons.append(f"collision:{result.blocked_reason}")

        # Marker interactions.
        for event in result.events:
            if event == "touched:reward_marker":
                valence += 1.0
                reasons.append("consumed_reward")
            elif event == "touched:danger_marker":
                valence -= 1.0
                reasons.append("touched_danger")
            elif event == "touched:unknown_marker":
                valence += 0.4
                reasons.append("novelty")
            elif event == "on:danger_marker":
                valence -= 0.8
                reasons.append("standing_on_danger")
            elif event == "on:reward_marker":
                valence += 0.5
                reasons.append("standing_on_reward")

        # Gradients: moving closer to reward is good, closer to danger is bad.
        if result.moved:
            dr_before, dr_after = before.get("dist_reward"), after.get("dist_reward")
            if dr_before is not None and dr_after is not None and dr_after < dr_before:
                valence += 0.5
                reasons.append("closer_to_reward")
            dd_before, dd_after = before.get("dist_danger"), after.get("dist_danger")
            if dd_before is not None and dd_after is not None:
                if dd_after < dd_before:
                    valence -= 0.4
                    reasons.append("closer_to_danger")
                elif dd_after > dd_before and dd_before <= 2:
                    valence += 0.3
                    reasons.append("escaped_danger")

        # Rest: restorative when needed, mildly useless at full energy.
        if result.action == "rest":
            if before.get("energy_low"):
                valence += 0.6
                reasons.append("needed_rest")
            elif before.get("energy_full"):
                valence -= 0.2
                reasons.append("needless_rest")

        # Useless repetition: same action, nothing moved, nothing changed.
        useless = (not result.moved and not result.environment_changed
                   and result.action not in ("rest",))
        self._recent.append(result.action if useless else f"!{result.action}")
        self._recent = self._recent[-self.useless_repeat_limit:]
        if (len(self._recent) == self.useless_repeat_limit
                and len(set(self._recent)) == 1
                and not self._recent[0].startswith("!")):
            valence -= 0.3
            reasons.append("useless_repetition")
            self.useless_repeats += 1

        if not reasons:
            self.last_reasons: List[str] = []
            return None
        self.last_reasons = reasons
        return C.Reaction(origin="embodiment", valence=clamp(valence, -1.0, 1.0))
