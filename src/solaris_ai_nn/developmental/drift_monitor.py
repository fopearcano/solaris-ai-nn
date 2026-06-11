"""Long-run drift monitor -- slow drift is life, fast drift is a warning,
zero drift may be a corpse.

Tracks drift across substrate state, readout parameters, habit weights,
executive scoring, homeostatic variables, world-model structure,
prediction accuracy, Mysterium pressure, identity anchors, and boundary
violations. Velocities are classified per metric and overall: healthy
slow adaptation, fast uncontrolled drift (warning), or inert flatness
(also a warning -- a system that never moves may be dead).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DRIFT_METRIC_NAMES = (
    "substrate_state_norm", "readout_weight_norm", "habit_weight_total",
    "executive_score_mean", "homeostatic_tension",
    "world_model_node_count", "prediction_accuracy",
    "mysterium_pressure", "identity_continuity",
    "boundary_violation_count",
)

FAST_THRESHOLD = 0.5   # |relative velocity| above this warns
INERT_WINDOWS = 5      # this many all-flat windows warns


@dataclass
class DriftMetric:
    name: str
    previous: float = 0.0
    current: float = 0.0
    delta: float = 0.0
    velocity: float = 0.0  # relative change per window

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DriftReport:
    """One window's drift verdict."""

    metrics: List[DriftMetric] = field(default_factory=list)
    classification: str = "healthy_slow"  # healthy_slow | fast_warning |
    #                                       inert_warning
    warnings: List[str] = field(default_factory=list)
    drift_velocity: float = 0.0  # mean |velocity| across metrics
    lifetime_s: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {**{k: v for k, v in self.__dict__.items()
                   if k != "metrics"},
                "metrics": [m.to_dict() for m in self.metrics]}


@dataclass
class LongRunDriftMonitor:
    """Compares metric windows; classifies the movement."""

    previous: Dict[str, float] = field(default_factory=dict)
    reports: List[DriftReport] = field(default_factory=list)
    flat_windows: int = field(default=0, init=False)
    fast_warnings_total: int = field(default=0, init=False)

    def observe(self, values: Dict[str, Any],
                lifetime_s: float = 0.0) -> DriftReport:
        current = {k: float(v) for k, v in values.items()
                   if isinstance(v, (int, float))}
        report = DriftReport(lifetime_s=lifetime_s)
        velocities: List[float] = []
        for name, value in sorted(current.items()):
            previous = self.previous.get(name, value)
            delta = value - previous
            scale = max(abs(previous), 1.0)
            velocity = round(delta / scale, 6)
            velocities.append(abs(velocity))
            metric = DriftMetric(name=name, previous=previous,
                                 current=value, delta=round(delta, 6),
                                 velocity=velocity)
            report.metrics.append(metric)
            if abs(velocity) > FAST_THRESHOLD and self.previous:
                report.warnings.append(
                    f"{name} moved fast (velocity {velocity:+.2f}); "
                    "uncontrolled drift is a warning")
        report.drift_velocity = (round(sum(velocities)
                                       / len(velocities), 6)
                                 if velocities else 0.0)
        if report.warnings:
            report.classification = "fast_warning"
            self.fast_warnings_total += 1
            self.flat_windows = 0
        elif self.previous and report.drift_velocity < 1e-9:
            self.flat_windows += 1
            if self.flat_windows >= INERT_WINDOWS:
                report.classification = "inert_warning"
                report.warnings.append(
                    f"no drift at all for {self.flat_windows} windows; "
                    "a system that never moves may be inert/dead")
        else:
            self.flat_windows = 0
        self.previous = current
        self.reports.append(report)
        self.reports = self.reports[-200:]
        return report

    # -- views --------------------------------------------------------------------

    def latest(self) -> Optional[DriftReport]:
        return self.reports[-1] if self.reports else None

    def mean_drift_velocity(self, window: int = 10) -> float:
        tail = self.reports[-window:]
        if not tail:
            return 0.0
        return round(sum(r.drift_velocity for r in tail) / len(tail), 6)

    def snapshot(self) -> Dict[str, Any]:
        latest = self.latest()
        return {
            "observations": len(self.reports),
            "latest_classification": (latest.classification
                                      if latest else None),
            "drift_velocity": self.mean_drift_velocity(),
            "fast_warnings_total": self.fast_warnings_total,
            "flat_windows": self.flat_windows,
            "tracked_metrics": list(DRIFT_METRIC_NAMES),
            "note": "slow drift is expected adaptation; fast drift and "
                    "total flatness are both warnings",
        }
