"""InnerMapObserver -- builds an :class:`InnerMapModel` by observing the substrate.

The observer is strictly read-only: it inspects a :class:`SolarisNeuralBridge`,
a :class:`ContinuousRunner`, telemetry, memory, habit, and synthesis, and
assembles a self-model. It never calls anything that advances or mutates the
substrate (no ``process``/``react``/``update`` of the bridge). This is the NN
analogue of Solaris_Ai's Inner MAP being a passive listener.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..memory.consolidation import MemoryConsolidator
from ..memory.trace_memory import TraceMemory
from ..utils.math import clamp, norm
from .boundaries import BoundaryRegistry
from .model import (
    BoundaryState,
    ContinuityState,
    InnerMapModel,
    MemoryState,
    ModuleState,
    NeuralSubstrateState,
    PlasticityState,
    TendencyState,
    UnknownState,
)

if TYPE_CHECKING:
    from ..bridges.neural_bridge import SolarisNeuralBridge
    from ..plasticity.habit_reinforcement import HabitReinforcement
    from ..plasticity.synthesis_pruning import SynthesisPruner
    from ..runtime.continuous_runner import ContinuousRunner


@dataclass
class InnerMapObserver:
    """Observes the substrate and produces an Inner MAP self-model.

    Any of the references may be omitted; the observer reports what it can see.
    If a bridge is given, ``memory``/``habit`` default to the bridge's own.
    """

    bridge: Optional["SolarisNeuralBridge"] = None
    runner: Optional["ContinuousRunner"] = None
    memory: Optional[TraceMemory] = None
    habit: Optional["HabitReinforcement"] = None
    synthesis: Optional["SynthesisPruner"] = None
    boundaries: BoundaryRegistry = field(default_factory=BoundaryRegistry)
    system_name: str = "solaris-ai-nn"
    version: str = "0.1.0"

    def __post_init__(self) -> None:
        self.consolidator = MemoryConsolidator()
        self._prev_reservoir_norm: Optional[float] = None
        self._model: Optional[InnerMapModel] = None
        if self.bridge is not None:
            if self.memory is None:
                self.memory = self.bridge.trace
            if self.habit is None:
                self.habit = self.bridge.habit
        if self.synthesis is None and self.runner is not None:
            self.synthesis = self.runner.synthesis

    # -- public observe_* (return dicts) -----------------------------------

    def observe_bridge(self, bridge: "SolarisNeuralBridge") -> Dict[str, Any]:
        return {
            "neural": asdict(self._neural(bridge)),
            "tendencies": asdict(self._tendencies(bridge)),
            "modules": [asdict(m) for m in self._bridge_modules(bridge)],
        }

    def observe_runner(self, runner: "ContinuousRunner") -> Dict[str, Any]:
        return {
            "continuity": asdict(self._continuity(runner)),
            "boundaries": asdict(self._boundaries(runner)),
            "identity": {
                "run_id": runner.run_id,
                "session_id": runner.session_id,
                "created_at": runner.created_at,
            },
        }

    def observe_memory(self, memory: TraceMemory) -> Dict[str, Any]:
        report = self.consolidator.consolidate(memory)
        return {"memory": asdict(self.consolidator.to_memory_state(report)),
                "report": report.to_dict()}

    def observe_plasticity(
        self, habit: "HabitReinforcement", synthesis: Optional["SynthesisPruner"] = None
    ) -> Dict[str, Any]:
        return {"plasticity": asdict(self._plasticity(habit, synthesis))}

    # -- builders (return dataclasses) -------------------------------------

    def _neural(self, bridge: "SolarisNeuralBridge") -> NeuralSubstrateState:
        esn = bridge.esn
        # Actual sparsity of the recurrent matrix (fraction non-zero).
        total = esn.n_reservoir * esn.n_reservoir
        nonzero = sum(1 for row in esn.W for w in row if w != 0.0)
        sparsity = (nonzero / total) if total else 0.0
        desire = bridge.suggest_desire()
        return NeuralSubstrateState(
            reservoir_size=esn.n_reservoir,
            reservoir_state_norm=norm(esn.state),
            reservoir_sparsity=sparsity,
            input_vector_size=esn.n_inputs,
            readout_output_size=bridge.readout.n_outputs,
            readout_weight_norm=bridge.readout.weight_magnitude(),
            prediction_confidence=desire.confidence if desire else 0.0,
            average_prediction_error=bridge.telemetry.average_prediction_error,
        )

    def _tendencies(self, bridge: "SolarisNeuralBridge") -> TendencyState:
        action = bridge.suggest_action()
        desire = bridge.suggest_desire()
        tendency_vector: Optional[List[float]] = None
        last_features = getattr(bridge, "_last_features", None)
        if last_features is not None:
            tendency_vector = bridge.readout.predict(last_features)
        logos = getattr(bridge, "_logos", None)
        logos_influence = None
        if logos is not None:
            logos_influence = {
                "division": logos.division,
                "union": logos.union,
                "fracture": logos.fracture,
            }
        confidence = desire.confidence if desire else 0.0
        return TendencyState(
            suggested_desire=desire.proposal if desire else None,
            suggested_action=action.name if action else None,
            action_tendency_vector=tendency_vector,
            exploration_tendency=bridge.exploration,
            stabilization_tendency=confidence,
            logos_modulation_influence=logos_influence,
        )

    def _bridge_modules(self, bridge: "SolarisNeuralBridge") -> List[ModuleState]:
        esn = bridge.esn
        return [
            ModuleState("reservoir", "ESN temporal substrate", metrics={
                "size": esn.n_reservoir, "state_norm": round(norm(esn.state), 4),
                "spectral_radius": esn.achieved_spectral_radius}),
            ModuleState("readout", "linear action tendencies", metrics={
                "outputs": bridge.readout.n_outputs,
                "weight_norm": round(bridge.readout.weight_magnitude(), 4),
                "nonzero_weights": bridge.readout.nonzero_count()}),
            ModuleState("habit", "reinforced pathways", metrics={
                "pathways": len(bridge.habit.weights),
                "strong": bridge.habit.strong_count()}),
            ModuleState("encoder", "event -> vector", metrics={
                "vector_size": bridge.encoder.vector_size}),
        ]

    def _continuity(self, runner: "ContinuousRunner") -> ContinuityState:
        lc = runner.lifecycle.snapshot()
        tele = runner.telemetry
        return ContinuityState(
            alive=lc.get("alive", True),
            lifecycle_state=lc.get("state", "unknown"),
            lifetime_steps=tele.lifetime_steps,
            session_steps=tele.steps,
            restart_count=runner.restart_count,
            last_heartbeat_ts=runner.lifecycle.last_heartbeat_ts,
            last_checkpoint_ts=getattr(runner, "_last_checkpoint_ts", 0.0),
            brain_death_gap_seconds=tele.brain_death_gap_seconds,
            graceful_previous_shutdown=tele.unexpected_deaths == 0,
        )

    def _boundaries(self, runner: "ContinuousRunner") -> BoundaryState:
        return BoundaryState(
            max_reservoir_size=runner.bridge.esn.n_reservoir,
            max_trace_length=runner.bridge.trace.capacity,
            max_runtime_duration=runner.max_duration_s,
            max_steps=runner.max_steps,
            continuous_mode_allowed=runner.continuous,
            cpu_only=True,
            no_heavy_ml_frameworks=True,
            action_authority_suggest_only=True,
        )

    def _plasticity(
        self, habit: "HabitReinforcement", synthesis: Optional["SynthesisPruner"]
    ) -> PlasticityState:
        # Strongest habits by |weight|.
        ranked = sorted(habit.weights.items(), key=lambda kv: abs(kv[1]), reverse=True)
        strongest = [
            {"pattern": k[0], "action": k[1], "weight": round(v, 4)}
            for k, v in ranked[:5]
        ]
        # Most repeated mappings by observation count.
        repeated = sorted(habit.counts.items(), key=lambda kv: kv[1], reverse=True)
        most_repeated = [
            {"pattern": k[0], "action": k[1], "count": c} for k, c in repeated[:5]
        ]
        pruning_history = list(getattr(self.runner, "pruning_history", []) or [])
        removed = sum(int(p.get("removed", 0)) for p in pruning_history)
        last_report = pruning_history[-1] if pruning_history else None
        readout = self.bridge.readout if self.bridge is not None else None
        subtraction_ratio = 0.0
        if readout is not None:
            total = readout.n_outputs * readout.n_features
            zeros = total - readout.nonzero_count()
            subtraction_ratio = zeros / total if total else 0.0
        return PlasticityState(
            habit_pathways=len(habit.weights),
            strongest_habits=strongest,
            most_repeated_mappings=most_repeated,
            habit_reinforcement_count=(
                self.bridge.telemetry.habit_reinforcements if self.bridge else 0
            ),
            pruning_count=len(pruning_history),
            last_pruning_report=last_report,
            removed_pathway_count=removed,
            subtraction_ratio=subtraction_ratio,
        )

    def _unknown(self, bridge: Optional["SolarisNeuralBridge"], memory_report) -> UnknownState:
        drift = 0.0
        if bridge is not None:
            current = norm(bridge.esn.state)
            if self._prev_reservoir_norm is not None:
                drift = abs(current - self._prev_reservoir_norm)
            self._prev_reservoir_norm = current
        recent_err = bridge.telemetry.recent_prediction_error if bridge else 0.0
        novelty = 0.0
        if memory_report is not None and memory_report.events_considered:
            novelty = clamp(memory_report.absence_count / memory_report.events_considered, 0.0, 1.0)
        return UnknownState(
            state_drift_score=drift,
            novelty_estimate=novelty,
            unexplained_error_estimate=recent_err,
            unknown_pressure=clamp(recent_err / 2.0, 0.0, 1.0),
        )

    # -- assemble / snapshot -----------------------------------------------

    def update(self) -> InnerMapModel:
        """Assemble a full :class:`InnerMapModel` from the observed components."""
        model = InnerMapModel(system_name=self.system_name, version=self.version)

        if self.runner is not None:
            model.run_id = self.runner.run_id
            model.session_id = self.runner.session_id
            model.created_at = self.runner.created_at
            model.continuity = self._continuity(self.runner)
            model.boundaries = self._boundaries(self.runner)
        elif self.bridge is not None:
            model.boundaries = BoundaryState(
                max_reservoir_size=self.bridge.esn.n_reservoir,
                max_trace_length=self.bridge.trace.capacity,
            )

        if self.bridge is not None:
            model.neural = self._neural(self.bridge)
            model.tendencies = self._tendencies(self.bridge)
            model.modules = self._bridge_modules(self.bridge)

        memory_report = None
        if self.memory is not None:
            memory_report = self.consolidator.consolidate(self.memory)
            model.memory = self.consolidator.to_memory_state(memory_report)

        if self.habit is not None:
            model.plasticity = self._plasticity(self.habit, self.synthesis)

        model.unknown = self._unknown(self.bridge, memory_report)
        model.touch()
        self._model = model
        return model

    def snapshot(self) -> Dict[str, Any]:
        """Return the latest model as a dict (computing one if needed)."""
        model = self._model or self.update()
        return model.to_dict()
