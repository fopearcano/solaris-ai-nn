"""Homeostatic variables -- normalized internal conditions with targets.

Seven groups (continuity, energy, safety, novelty/Mysterium, memory,
social/sidecar, embodiment) of named variables, each normalized to [0, 1]
where possible, with a target (or target range), a trend, a deviation, and
an urgency. Raw source values are never hidden -- they live in metadata.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize(value: float, low: float, high: float) -> float:
    """Map ``value`` from [low, high] into [0, 1], clamped."""
    if high <= low:
        return 0.0
    return clamp01((float(value) - low) / (high - low))


class VariableTrend:
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"

    ALL = (RISING, FALLING, STABLE, UNKNOWN)


@dataclass
class VariableRange:
    """Bounds and target for one variable (target may be a point or range)."""

    minimum: float = 0.0
    maximum: float = 1.0
    target: Optional[float] = None
    target_range: Optional[Tuple[float, float]] = None

    def deviation(self, value: float) -> float:
        """Distance from the target (or range edge), in normalized units."""
        if self.target_range is not None:
            low, high = self.target_range
            if low <= value <= high:
                return 0.0
            return round(min(abs(value - low), abs(value - high)), 4)
        target = self.target if self.target is not None else self.minimum
        return round(abs(value - target), 4)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# group -> {variable name: (target or (lo, hi) range, urgency weight)}
# Pressure-style variables target 0.0; freshness/health-style target 1.0.
VARIABLE_GROUPS: Dict[str, Dict[str, Tuple[Any, float]]] = {
    "continuity": {
        "heartbeat_freshness": (1.0, 1.5),
        "checkpoint_freshness": (1.0, 1.0),
        "restart_stability": (1.0, 1.0),
        "operational_health": (1.0, 1.2),
        "identity_uncertainty_pressure": (0.0, 1.0),  # ego (Prompt 18)
    },
    "energy": {
        "body_energy": (1.0, 1.2),
        "update_budget": (1.0, 0.6),
        "fatigue": (0.0, 0.8),
    },
    "safety": {
        "incident_pressure": (0.0, 1.2),
        "blocked_action_pressure": (0.0, 1.0),
        "policy_violation_pressure": (0.0, 1.5),
        "unsafe_proposal_pressure": (0.0, 1.0),
        "boundary_violation_pressure": (0.0, 1.3),  # ego (Prompt 18)
        "self_model_uncertainty_pressure": (0.0, 0.6),  # ego (Prompt 18)
        "drift_pressure": (0.0, 0.8),  # developmental (Prompt 21)
    },
    "novelty": {
        "unknown_pressure": (0.0, 0.8),
        "prediction_miss_pressure": (0.0, 0.8),
        "novelty_pressure": ((0.1, 0.5), 0.5),  # some novelty is healthy
        "replay_mismatch_pressure": (0.0, 1.0),
        "stagnation_pressure": (0.0, 0.6),  # developmental (Prompt 21)
    },
    "memory": {
        "trace_pressure": (0.0, 0.6),
        "consolidation_pressure": (0.0, 0.7),
        "world_unknown_ratio": (0.0, 0.6),
        "graph_redundancy_pressure": (0.0, 0.5),
    },
    "social": {
        "external_signal_pressure": ((0.1, 0.8), 0.5),
        "suggestion_feedback_pressure": (0.0, 0.5),
        "sidecar_observation_pressure": (0.0, 0.4),
        "operator_pressure": (0.0, 1.0),
    },
    "embodiment": {
        "obstacle_pressure": (0.0, 0.8),
        "reward_proximity": (0.0, 0.6),   # high proximity is opportunity
        "danger_proximity": (0.0, 1.4),
        "exhaustion_pressure": (0.0, 1.2),
        "low_stimulus_pressure": (0.0, 0.6),
    },
}

VARIABLE_TO_GROUP: Dict[str, str] = {
    name: group for group, members in VARIABLE_GROUPS.items()
    for name in members
}


@dataclass
class HomeostaticVariable:
    """One normalized internal condition."""

    name: str
    value: float = 0.0
    range: VariableRange = field(default_factory=VariableRange)
    trend: str = VariableTrend.UNKNOWN
    deviation: float = 0.0
    urgency: float = 0.0
    urgency_weight: float = 1.0
    source_modules: List[str] = field(default_factory=list)
    last_updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _history: List[float] = field(default_factory=list, repr=False)

    def update(self, value: float, source: str = "",
               raw: Any = None, **metadata: Any) -> "HomeostaticVariable":
        self.value = clamp01(value)
        self._history.append(self.value)
        self._history = self._history[-20:]
        self.trend = self._trend()
        self.deviation = self.range.deviation(self.value)
        self.urgency = round(clamp01(self.deviation * self.urgency_weight), 4)
        self.last_updated_at = time.time()
        if source and source not in self.source_modules:
            self.source_modules.append(source)
            self.source_modules = self.source_modules[:8]
        if raw is not None:
            self.metadata["raw_value"] = raw  # never hide the source value
        for key, val in metadata.items():
            self.metadata[key] = val
        return self

    def _trend(self) -> str:
        if len(self._history) < 3:
            return VariableTrend.UNKNOWN
        delta = self._history[-1] - self._history[-3]
        if delta > 0.02:
            return VariableTrend.RISING
        if delta < -0.02:
            return VariableTrend.FALLING
        return VariableTrend.STABLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "value": self.value,
            "range": self.range.to_dict(), "trend": self.trend,
            "deviation": self.deviation, "urgency": self.urgency,
            "source_modules": list(self.source_modules),
            "last_updated_at": self.last_updated_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class HomeostaticState:
    """All variables, grouped, with the most-deviant on top."""

    variables: Dict[str, HomeostaticVariable] = field(default_factory=dict)

    def upsert(self, name: str, value: float, source: str = "",
               raw: Any = None, **metadata: Any) -> HomeostaticVariable:
        variable = self.variables.get(name)
        if variable is None:
            spec = VARIABLE_GROUPS.get(VARIABLE_TO_GROUP.get(name, ""),
                                       {}).get(name)
            var_range = VariableRange()
            weight = 1.0
            if spec is not None:
                target, weight = spec
                if isinstance(target, tuple):
                    var_range = VariableRange(target_range=target)
                else:
                    var_range = VariableRange(target=float(target))
            variable = HomeostaticVariable(name=name, range=var_range,
                                           urgency_weight=weight)
            self.variables[name] = variable
        return variable.update(value, source=source, raw=raw, **metadata)

    def get(self, name: str) -> Optional[HomeostaticVariable]:
        return self.variables.get(name)

    def value(self, name: str, default: float = 0.0) -> float:
        variable = self.variables.get(name)
        return variable.value if variable is not None else default

    def group(self, group_name: str) -> List[HomeostaticVariable]:
        return [v for name, v in sorted(self.variables.items())
                if VARIABLE_TO_GROUP.get(name) == group_name]

    def most_urgent(self, limit: int = 5) -> List[HomeostaticVariable]:
        ranked = sorted(self.variables.values(),
                        key=lambda v: (-v.urgency, v.name))
        return ranked[:limit]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variables": {name: v.to_dict()
                          for name, v in sorted(self.variables.items())},
            "most_urgent": [v.name for v in self.most_urgent(5)],
        }
