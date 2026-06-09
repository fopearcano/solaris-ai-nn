"""Synthesis through subtraction -- pruning weak pathways.

This mirrors ``solaris/modules/synthesis.py``, where the explicit principle is:

    "Synthesis proceeds by Subtraction."

Synthesis here is **not** generic compression. It is the deliberate *removal* of
weak or unused pathways so the substrate is defined as much by what it has let
go of as by what it retains. Every removal is logged with a reason, and the
module exposes a "subtraction report" so the act of forgetting is observable.

Two surfaces are pruned:

* readout weights below a magnitude threshold (zeroed in place)
* habit pathways below a magnitude threshold (delegated to HabitReinforcement)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .habit_reinforcement import HabitReinforcement
from ..reservoir.readout import LinearReadout


@dataclass
class Removal:
    """A single subtracted element and the reason it was removed."""

    target: str  # e.g. "readout[2][41]" or "habit(Stimulus:3, action_1)"
    value: float  # the magnitude that was removed
    reason: str


@dataclass
class SubtractionReport:
    """What synthesis removed in one pass, and why.

    Attributes:
        removed: Per-element removal records.
        readout_zeroed: Count of readout weights set to zero.
        habits_forgotten: Count of habit pathways dropped.
        threshold: The magnitude threshold used this pass.
    """

    removed: List[Removal] = field(default_factory=list)
    readout_zeroed: int = 0
    habits_forgotten: int = 0
    threshold: float = 0.0

    @property
    def total_removed(self) -> int:
        """Total number of subtracted elements."""
        return self.readout_zeroed + self.habits_forgotten

    def summary(self) -> str:
        """One-line human summary of the subtraction."""
        return (
            f"synthesis subtracted {self.total_removed} pathways "
            f"(readout={self.readout_zeroed}, habits={self.habits_forgotten}) "
            f"at threshold {self.threshold:.4f}"
        )


@dataclass
class SynthesisPruner:
    """Detects and removes weak pathways, returning a subtraction report.

    Args:
        readout_threshold: |weight| below which a readout weight is zeroed.
        habit_threshold: |bias| below which a habit pathway is forgotten.
        detail_limit: Max number of individual ``Removal`` records to keep per
            pass (the counts are always exact; details are capped to stay light).
    """

    readout_threshold: float = 0.01
    habit_threshold: float = 0.05
    detail_limit: int = 32

    def prune(
        self,
        readout: LinearReadout,
        habit: Optional[HabitReinforcement] = None,
    ) -> SubtractionReport:
        """Run one synthesis pass over readout (and optionally habit) weights."""
        report = SubtractionReport(threshold=self.readout_threshold)

        for i, row in enumerate(readout.weights):
            for j, w in enumerate(row):
                if w != 0.0 and abs(w) < self.readout_threshold:
                    if len(report.removed) < self.detail_limit:
                        report.removed.append(
                            Removal(
                                target=f"readout[{i}][{j}]",
                                value=w,
                                reason="below readout magnitude threshold",
                            )
                        )
                    row[j] = 0.0
                    report.readout_zeroed += 1

        if habit is not None:
            # Record a few details before delegating the bulk removal.
            for key, w in list(habit.weights.items()):
                if abs(w) < self.habit_threshold and len(report.removed) < self.detail_limit:
                    report.removed.append(
                        Removal(
                            target=f"habit{key}",
                            value=w,
                            reason="below habit magnitude threshold",
                        )
                    )
            report.habits_forgotten = habit.prune_below(self.habit_threshold)

        return report
