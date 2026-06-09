"""Habit reinforcement -- a neural-experimental echo of Solaris_Ai's Habit.

Mirrors ``solaris/modules/habit.py``: it maintains per-(situation, action) bias
scalars in [-1, +1] that move toward observed reaction valence::

    new = clamp(old + lr * valence, -1, +1)

These biases lightly tilt action selection toward pathways that have repeatedly
paid off, *without* retraining the reservoir or readout. That is the point:
habit is a cheap, separable form of plasticity layered on top of the substrate.

The "situation" is a coarse pattern key from the event encoder, so habits
reinforce *kinds of situations*, not unique events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from ..utils.math import clamp

PathwayKey = Tuple[str, str]  # (pattern_key, action_label)


@dataclass
class HabitReinforcement:
    """Tracks and reinforces repeated (situation, action) pathways.

    Args:
        lr: Reinforcement rate -- how fast a bias moves toward valence.
        bias_scale: Multiplier applied when turning biases into a readout offset
            (kept small so habit *nudges* rather than overrides the readout).
    """

    lr: float = 0.2
    bias_scale: float = 0.25
    weights: Dict[PathwayKey, float] = field(default_factory=dict)
    counts: Dict[PathwayKey, int] = field(default_factory=dict)

    def observe(self, pattern_key: str, action_label: str, valence: float) -> float:
        """Reinforce a pathway after an action received a reaction.

        Returns the updated bias for the pathway.
        """
        key = (pattern_key, action_label)
        old = self.weights.get(key, 0.0)
        new = clamp(old + self.lr * valence, -1.0, 1.0)
        self.weights[key] = new
        self.counts[key] = self.counts.get(key, 0) + 1
        return new

    def bias_for(self, pattern_key: str, action_label: str) -> float:
        """Current bias scalar for a pathway (0.0 if never seen)."""
        return self.weights.get((pattern_key, action_label), 0.0)

    def bias_vector(self, pattern_key: str, action_labels: List[str]) -> List[float]:
        """Per-action additive offset for the readout, scaled by ``bias_scale``."""
        return [
            self.bias_scale * self.bias_for(pattern_key, label)
            for label in action_labels
        ]

    def strong_count(self, threshold: float = 0.5) -> int:
        """Number of pathways whose |bias| exceeds ``threshold``."""
        return sum(1 for w in self.weights.values() if abs(w) > threshold)

    def prune_below(self, threshold: float) -> int:
        """Forget pathways with |bias| below ``threshold``. Returns count removed.

        This is the habit-side counterpart to synthesis-through-subtraction:
        weak, unrewarded habits are dropped rather than carried forever.
        """
        weak = [k for k, w in self.weights.items() if abs(w) < threshold]
        for k in weak:
            del self.weights[k]
            self.counts.pop(k, None)
        return len(weak)

    def total_weight(self) -> float:
        """Sum of |bias| across all pathways (a coarse "habit mass" metric)."""
        return sum(abs(w) for w in self.weights.values())
