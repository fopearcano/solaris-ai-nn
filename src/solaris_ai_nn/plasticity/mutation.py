"""Plasticity data model + the live-parameter target registry.

A *plasticity step* is one proposed, validated, and (maybe) applied change to a
runtime parameter or learning pathway -- never to source code. Every step is a
self-contained record: what changed, from what to what, why, whether it was safe,
and how to undo it. The :class:`TargetRegistry` is the only thing that actually
reads and writes live parameters, so it is also the single seam used for
rollback.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from ..bridges.neural_bridge import SolarisNeuralBridge
    from ..plasticity.synthesis_pruning import SynthesisPruner

# Supported target components (section 3).
RESERVOIR = "reservoir"
READOUT = "readout"
HABIT = "habit"
SYNTHESIS = "synthesis"
BRIDGE = "bridge"
EXPERIMENT_LOOP = "experiment_loop"
INNER_MAP = "inner_map"
BOUNDARIES = "boundaries"

SUPPORTED_TARGETS = frozenset(
    {RESERVOIR, READOUT, HABIT, SYNTHESIS, BRIDGE, EXPERIMENT_LOOP, INNER_MAP, BOUNDARIES}
)

# Step status values.
PROPOSED = "proposed"
APPLIED = "applied"
REJECTED = "rejected"
ROLLED_BACK = "rolled_back"


@dataclass
class PlasticityTarget:
    """Identifies what a step changes: a parameter on a component."""

    component: str
    parameter: str

    def key(self) -> Tuple[str, str]:
        return (self.component, self.parameter)

    def label(self) -> str:
        return f"{self.component}.{self.parameter}"


@dataclass
class PlasticityChange:
    """The before/after of a single parameter change."""

    old_value: Any = None
    new_value: Any = None
    expected_effect: str = ""


@dataclass
class PlasticityStep:
    """A complete, auditable plasticity step (section 3)."""

    target: PlasticityTarget
    change: PlasticityChange
    reason: str = ""
    trigger_source: str = "policy"
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    run_id: str = ""
    session_id: str = ""
    lifetime_step: int = 0
    observed_effect: Optional[Dict[str, Any]] = None
    safety_result: Optional[Dict[str, Any]] = None
    rollback_data: Any = None
    status: str = PROPOSED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlasticityStep":
        data = dict(data)
        target = data.pop("target", {})
        change = data.pop("change", {})
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in valid}
        return cls(
            target=PlasticityTarget(**target) if isinstance(target, dict) else target,
            change=PlasticityChange(**change) if isinstance(change, dict) else change,
            **kwargs,
        )


@dataclass
class PlasticityResult:
    """The outcome of applying or rolling back a step."""

    step_id: str
    status: str
    applied: bool
    message: str = ""
    old_value: Any = None
    new_value: Any = None
    safety: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Live-parameter target registry                                              #
# --------------------------------------------------------------------------- #

Getter = Callable[[], Any]
Setter = Callable[[Any], None]


@dataclass
class TargetRegistry:
    """Maps ``(component, parameter)`` to safe getters/setters over live objects.

    This is the *only* place that mutates live runtime parameters, so rollback
    routes through it too. Unknown targets are reported (not silently ignored).
    """

    bridge: "SolarisNeuralBridge"
    synthesis: Optional["SynthesisPruner"] = None
    runner: Any = None  # optional ContinuousRunner (for loop-level params)

    def __post_init__(self) -> None:
        self._map: Dict[Tuple[str, str], Tuple[Getter, Setter]] = {}
        self._build()

    def _build(self) -> None:
        b = self.bridge
        esn = b.esn

        def reg(component: str, param: str, getter: Getter, setter: Setter) -> None:
            self._map[(component, param)] = (getter, setter)

        # Reservoir (recomputable setters keep dynamics consistent).
        reg(RESERVOIR, "leak_rate", lambda: esn.leak_rate, esn.set_leak_rate)
        reg(RESERVOIR, "input_gain", lambda: esn.input_scaling, esn.set_input_scaling)
        reg(RESERVOIR, "spectral_radius",
            lambda: esn.achieved_spectral_radius, esn.set_spectral_radius)

        # Readout / online learner.
        reg(READOUT, "learning_rate", lambda: b.learner.lr,
            lambda v: setattr(b.learner, "lr", float(v)))
        reg(READOUT, "regularization", lambda: b.learner.weight_clip,
            lambda v: setattr(b.learner, "weight_clip", float(v)))
        reg(READOUT, "confidence_threshold", lambda: b.confidence_threshold,
            lambda v: setattr(b, "confidence_threshold", float(v)))

        # Habit.
        reg(HABIT, "reinforcement_rate", lambda: b.habit.lr,
            lambda v: setattr(b.habit, "lr", float(v)))
        reg(HABIT, "max_habit_weight", lambda: b.habit.max_weight,
            lambda v: setattr(b.habit, "max_weight", float(v)))
        reg(HABIT, "decay_rate", lambda: b.habit.decay,
            lambda v: setattr(b.habit, "decay", float(v)))

        # Synthesis.
        if self.synthesis is not None:
            syn = self.synthesis
            reg(SYNTHESIS, "pruning_threshold", lambda: syn.readout_threshold,
                lambda v: setattr(syn, "readout_threshold", float(v)))
            reg(SYNTHESIS, "max_prune_fraction", lambda: syn.max_prune_fraction,
                lambda v: setattr(syn, "max_prune_fraction", float(v)))
        if self.runner is not None:
            reg(SYNTHESIS, "pruning_interval", lambda: self.runner.prune_interval_steps,
                lambda v: setattr(self.runner, "prune_interval_steps", int(v)))
            reg(EXPERIMENT_LOOP, "silence_threshold", lambda: self.runner.silence_threshold,
                lambda v: setattr(self.runner, "silence_threshold", int(v)))

        # Bridge tendencies.
        reg(BRIDGE, "exploration_tendency", lambda: b.exploration,
            lambda v: setattr(b, "exploration", float(v)))
        reg(BRIDGE, "stabilization_tendency", lambda: b.stabilization,
            lambda v: setattr(b, "stabilization", float(v)))
        reg(BRIDGE, "suggestion_threshold", lambda: b.suggestion_threshold,
            lambda v: setattr(b, "suggestion_threshold", float(v)))

    # -- access -------------------------------------------------------------

    def has(self, target: PlasticityTarget) -> bool:
        if target.parameter.startswith("weight:") and target.component == HABIT:
            return True
        return target.key() in self._map

    def get(self, target: PlasticityTarget) -> Any:
        if target.component == HABIT and target.parameter.startswith("weight:"):
            return self.bridge.habit.weights.get(self._habit_key(target), 0.0)
        if not self.has(target):
            raise KeyError(f"no mutable parameter {target.label()!r}")
        return self._map[target.key()][0]()

    def set(self, target: PlasticityTarget, value: Any) -> Any:
        """Set ``target`` to ``value``; return the previous value (for rollback)."""
        old = self.get(target)
        if target.component == HABIT and target.parameter.startswith("weight:"):
            self.bridge.habit.weights[self._habit_key(target)] = float(value)
            return old
        self._map[target.key()][1](value)
        return old

    @staticmethod
    def _habit_key(target: PlasticityTarget) -> Tuple[str, str]:
        raw = target.parameter[len("weight:"):]
        pattern, _, action = raw.partition("|")
        return (pattern, action)

    # -- snapshot for Inner MAP / checkpoint -------------------------------

    def snapshot_values(self) -> List[List[Any]]:
        """All registered parameter values as ``[component, parameter, value]``."""
        return [[c, p, getter()] for (c, p), (getter, _setter) in self._map.items()]

    def current_values(self) -> Dict[str, Any]:
        """Flat ``"component.parameter" -> value`` mapping (Inner MAP friendly)."""
        return {f"{c}.{p}": getter() for (c, p), (getter, _s) in self._map.items()}

    def apply_values(self, values: List[List[Any]]) -> None:
        """Restore parameter values produced by :meth:`snapshot_values`."""
        for entry in values:
            if len(entry) != 3:
                continue
            component, parameter, value = entry
            tgt = PlasticityTarget(component, parameter)
            if self.has(tgt):
                try:
                    self.set(tgt, value)
                except (KeyError, ValueError):
                    continue
