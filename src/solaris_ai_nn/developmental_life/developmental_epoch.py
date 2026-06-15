"""Developmental epochs -- explainable developmental slices that survive restart.

A :class:`DevelopmentalEpoch` is a developmental slice (NOT a biological "age").
Its :class:`EpochBoundary` records an explainable :class:`EpochTransitionReason`,
and epochs are persisted so they survive restart.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EpochTransitionReason:
    TIME_ELAPSED = "time_elapsed"
    SENSORY_FIELD_SHIFT = "sensory_field_shift"
    NEW_STABLE_CONCEPTS = "new_stable_proto_concepts"
    NEW_STABLE_SIGNS = "new_stable_signs"
    PREDICTION_IMPROVEMENT = "prediction_improvement"
    ACTION_EFFECT_LEARNING = "action_effect_learning"
    HABIT_STABILIZATION = "habit_stabilization"
    SOURCE_DIET_SHIFT = "source_diet_shift"
    OVERLOAD_DEPRIVATION_EVENT = "overload_deprivation_event"
    BOUNDARY_DISCONTINUITY = "boundary_discontinuity"
    LOGOS_TENSION_SPIKE = "LOGOS_tension_spike"
    PLATEAU_DETECTED = "plateau_detected"
    REGRESSION_DETECTED = "regression_detected"
    OPERATOR_CHECKPOINT = "operator_scheduled_checkpoint"
    UNKNOWN = "unknown"

    ALL = (TIME_ELAPSED, SENSORY_FIELD_SHIFT, NEW_STABLE_CONCEPTS,
           NEW_STABLE_SIGNS, PREDICTION_IMPROVEMENT, ACTION_EFFECT_LEARNING,
           HABIT_STABILIZATION, SOURCE_DIET_SHIFT, OVERLOAD_DEPRIVATION_EVENT,
           BOUNDARY_DISCONTINUITY, LOGOS_TENSION_SPIKE, PLATEAU_DETECTED,
           REGRESSION_DETECTED, OPERATOR_CHECKPOINT, UNKNOWN)


@dataclass
class EpochBoundary:
    reason: str
    detail: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"reason": self.reason, "detail": self.detail,
                "evidence_refs": list(self.evidence_refs)}


@dataclass
class EpochSummary:
    composite_growth: float = 0.0
    increased_dimensions: List[str] = field(default_factory=list)
    maturation_marker_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"composite_growth": round(self.composite_growth, 4),
                "increased_dimensions": list(self.increased_dimensions),
                "maturation_marker_count": self.maturation_marker_count}


@dataclass
class DevelopmentalEpoch:
    """One developmental slice (not a biological age); boundary is explainable."""

    epoch_index: int
    start_tick: int
    epoch_id: str = field(default_factory=lambda: f"EPOCH_{uuid.uuid4().hex[:8]}")
    end_tick: Optional[int] = None
    open_boundary: EpochBoundary = field(
        default_factory=lambda: EpochBoundary(EpochTransitionReason.TIME_ELAPSED))
    close_boundary: Optional[EpochBoundary] = None
    summary: EpochSummary = field(default_factory=EpochSummary)

    @property
    def closed(self) -> bool:
        return self.end_tick is not None

    def close(self, tick: int, boundary: EpochBoundary) -> None:
        self.end_tick = tick
        self.close_boundary = boundary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "epoch_index": self.epoch_index,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "closed": self.closed,
            "open_boundary": self.open_boundary.to_dict(),
            "close_boundary": (self.close_boundary.to_dict()
                               if self.close_boundary else None),
            "summary": self.summary.to_dict(),
            "note": "developmental slice, not a biological age; boundary is "
                    "explainable and persisted across restart",
        }
