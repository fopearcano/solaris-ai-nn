"""Post-pilot baseline comparison -- before vs after, conservatively read.

The :class:`BaselineComparator` builds two :class:`BaselineSnapshot`s (e.g.
initial vs final, day 1 vs day 30, week 1 vs week 4, dry-run vs real) and
produces a :class:`BaselineComparison` of their deltas. It is deliberately
conservative: more data, more symbols, more hypotheses, and more complexity
are *not* automatically growth, and simulated/real labels are preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Dimensions where a bare increase must NOT be read as growth on its own.
_COUNT_ONLY_DIMENSIONS = (
    "proto_symbol_count", "hypothesis_count", "world_model_node_count",
    "world_model_edge_count", "memory_layer_count",
    "active_perception_sampling_count", "logos_tension_count",
)
# Dimensions where a decrease is the desirable direction.
_LOWER_IS_BETTER = (
    "ambiguous_symbol_ratio", "world_model_contradiction_count",
    "stagnation_seconds", "drift_velocity", "safety_incident_count",
    "governance_block_count",
)


@dataclass
class BaselineSnapshot:
    """A point-in-time snapshot across the baseline dimensions."""

    label: str
    is_simulated: bool = False
    memory_layer_count: float = 0.0
    compression_ratio: float = 1.0
    proto_symbol_count: float = 0.0
    stable_symbol_count: float = 0.0
    ambiguous_symbol_ratio: float = 0.0
    world_model_node_count: float = 0.0
    world_model_edge_count: float = 0.0
    world_model_contradiction_count: float = 0.0
    hypothesis_count: float = 0.0
    supported_hypothesis_count: float = 0.0
    logos_tension_count: float = 0.0
    resolved_tension_count: float = 0.0
    habit_stability: float = 0.0
    prediction_score: float = 0.0
    mysterium_pressure: float = 0.0
    active_perception_usefulness: float = 0.0
    autoregeneration_event_count: float = 0.0
    safety_incident_count: float = 0.0
    governance_block_count: float = 0.0
    structural_change_score: float = 0.0
    stagnation_seconds: float = 0.0
    drift_velocity: float = 0.0
    identity_continuous: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def dimensions(self) -> Dict[str, float]:
        return {k: float(v) for k, v in self.__dict__.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)}

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class BaselineComparison:
    """The delta between a before and after snapshot, conservatively read."""

    before_label: str
    after_label: str
    simulated_mismatch: bool = False
    deltas: Dict[str, float] = field(default_factory=dict)
    count_only_increases: List[str] = field(default_factory=list)
    improved_dimensions: List[str] = field(default_factory=list)
    worsened_dimensions: List[str] = field(default_factory=list)
    identity_continuous: bool = True
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class BaselineComparator:
    """Builds snapshots from artifacts and compares them conservatively."""

    def snapshot_from(self, label: str, data: Dict[str, Any],
                      is_simulated: bool = False) -> BaselineSnapshot:
        """Build a snapshot from a flat dict of measured dimensions."""
        snap = BaselineSnapshot(label=label, is_simulated=is_simulated)
        for key, value in (data or {}).items():
            if hasattr(snap, key) and key not in ("label",):
                try:
                    if isinstance(getattr(snap, key), bool):
                        setattr(snap, key, bool(value))
                    elif isinstance(getattr(snap, key), (int, float)):
                        setattr(snap, key, float(value))
                    else:
                        setattr(snap, key, value)
                except (TypeError, ValueError):
                    continue
        return snap

    def compare(self, before: BaselineSnapshot,
                after: BaselineSnapshot) -> BaselineComparison:
        cmp = BaselineComparison(before_label=before.label,
                                 after_label=after.label)
        cmp.simulated_mismatch = before.is_simulated != after.is_simulated
        if cmp.simulated_mismatch:
            cmp.notes.append("before/after differ in simulated vs real time; "
                             "deltas are not directly comparable")
        cmp.identity_continuous = bool(before.identity_continuous
                                       and after.identity_continuous)
        b = before.dimensions()
        a = after.dimensions()
        for key in sorted(set(b) | set(a)):
            delta = round(a.get(key, 0.0) - b.get(key, 0.0), 6)
            cmp.deltas[key] = delta
            if delta == 0.0:
                continue
            if key in _LOWER_IS_BETTER:
                (cmp.improved_dimensions if delta < 0
                 else cmp.worsened_dimensions).append(key)
            elif key in _COUNT_ONLY_DIMENSIONS and delta > 0:
                cmp.count_only_increases.append(key)
                cmp.notes.append(
                    f"{key} increased by {delta}: a count increase is not, by "
                    "itself, evidence of growth")
            elif delta > 0:
                cmp.improved_dimensions.append(key)
            else:
                cmp.worsened_dimensions.append(key)
        return cmp

    def compare_dicts(self, before_label: str, before: Dict[str, Any],
                      after_label: str, after: Dict[str, Any],
                      before_simulated: bool = False,
                      after_simulated: bool = False) -> BaselineComparison:
        return self.compare(
            self.snapshot_from(before_label, before, before_simulated),
            self.snapshot_from(after_label, after, after_simulated))
