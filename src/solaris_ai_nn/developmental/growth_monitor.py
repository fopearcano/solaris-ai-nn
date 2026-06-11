"""Growth monitor -- is structure changing, or is data just piling up?

Tracks the long-horizon growth metrics (habits, world model, predictions,
Mysterium, pruning, schemas, replay, decision diversity, continuity,
stability) and classifies each observation window as accumulation,
consolidation, stabilization, pruning, regression, drift, phase
transition, or stagnation. The classification is a measurement label,
never a claim of development.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

GROWTH_CLASSIFICATIONS = (
    "accumulation", "consolidation", "stabilization", "pruning",
    "regression", "drift", "phase_transition", "stagnation",
)

# Metrics that indicate *structural* change (vs raw data volume).
STRUCTURE_METRICS = ("stable_habit_count", "habit_turnover",
                     "consolidated_schema_count", "pruning_count",
                     "executive_decision_diversity",
                     "world_model_edge_count")
DATA_METRICS = ("world_model_node_count", "latent_replay_count",
                "total_observed_stimuli")


@dataclass
class GrowthMetric:
    name: str
    value: float = 0.0
    delta: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class GrowthSnapshot:
    """One observation window, classified."""

    metrics: Dict[str, float] = field(default_factory=dict)
    deltas: Dict[str, float] = field(default_factory=dict)
    classification: str = "accumulation"
    structural_change_score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    lifetime_s: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class GrowthMonitor:
    """Observes metric dicts over time; classifies the latest window."""

    history: List[GrowthSnapshot] = field(default_factory=list)
    stagnation_windows: int = field(default=0, init=False)

    def observe(self, metrics: Dict[str, Any],
                lifetime_s: float = 0.0) -> GrowthSnapshot:
        values = {k: float(v) for k, v in metrics.items()
                  if isinstance(v, (int, float))}
        previous = self.history[-1].metrics if self.history else {}
        deltas = {k: round(values[k] - previous.get(k, 0.0), 6)
                  for k in values}
        snapshot = GrowthSnapshot(metrics=values, deltas=deltas,
                                  lifetime_s=lifetime_s)
        snapshot.structural_change_score = self._structural_score(deltas)
        snapshot.classification, snapshot.reasons = self._classify(
            values, deltas, snapshot.structural_change_score)
        if snapshot.classification == "stagnation":
            self.stagnation_windows += 1
        else:
            self.stagnation_windows = 0
        self.history.append(snapshot)
        self.history = self.history[-200:]
        return snapshot

    @staticmethod
    def _structural_score(deltas: Dict[str, float]) -> float:
        """Relative structural movement in [0, 1]; cautious by design."""
        total = 0.0
        counted = 0
        for name in STRUCTURE_METRICS:
            if name in deltas:
                total += min(1.0, abs(deltas[name]) / 5.0)
                counted += 1
        return round(total / counted, 4) if counted else 0.0

    def _classify(self, values: Dict[str, float],
                  deltas: Dict[str, float],
                  structural: float) -> "tuple[str, List[str]]":
        if not self.history:
            return ("accumulation", ["first observation window"])
        structure_moved = structural > 0.05
        data_moved = any(abs(deltas.get(name, 0.0)) > 0
                         for name in DATA_METRICS)
        if deltas.get("prediction_accuracy_trend", 0.0) < -0.15 \
                or deltas.get("stable_habit_count", 0.0) < -2:
            return ("regression", ["prediction accuracy or stable habits "
                                   "fell across the window"])
        if abs(deltas.get("prediction_accuracy_trend", 0.0)) > 0.3 \
                or abs(deltas.get("mysterium_trend", 0.0)) > 0.4:
            return ("phase_transition",
                    ["a metric jumped beyond the phase-transition "
                     "threshold; this is a candidate, not proof"])
        if deltas.get("pruning_count", 0.0) > 0 and not data_moved:
            return ("pruning", ["structure was subtracted without new "
                                "data volume"])
        if deltas.get("consolidated_schema_count", 0.0) > 0:
            return ("consolidation", ["consolidated schemas grew"])
        if not structure_moved and not data_moved:
            return ("stagnation", ["neither structure nor data volume "
                                   "moved this window"])
        if not structure_moved and data_moved:
            return ("accumulation", ["data volume grew but structural "
                                     "metrics did not move"])
        if structure_moved and abs(deltas.get("habit_turnover",
                                              0.0)) > 3:
            return ("drift", ["structural metrics are moving "
                              "continuously without consolidating"])
        if structure_moved and deltas.get("stable_habit_count",
                                          0.0) >= 0:
            return ("stabilization", ["structure moved and stable habits "
                                      "held or grew"])
        return ("accumulation", ["default: growth without classified "
                                 "structure change"])

    # -- views --------------------------------------------------------------------

    def stagnation_duration_windows(self) -> int:
        return self.stagnation_windows

    def latest(self) -> Optional[GrowthSnapshot]:
        return self.history[-1] if self.history else None

    def snapshot(self) -> Dict[str, Any]:
        latest = self.latest()
        return {
            "observations": len(self.history),
            "latest_classification": (latest.classification
                                      if latest else None),
            "structural_change_score": (latest.structural_change_score
                                        if latest else 0.0),
            "stagnation_windows": self.stagnation_windows,
            "classifications": list(GROWTH_CLASSIFICATIONS),
            "note": "growth labels are measurements over recorded "
                    "metrics, not claims of development",
        }
