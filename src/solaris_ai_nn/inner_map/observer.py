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
    sidecar: Any = None  # optional SolarisNNSidecar (duck-typed; observe-only)
    embodiment: Any = None  # optional object exposing embodiment_summary()
    evaluation: Any = None  # optional dict or object with evaluation_summary()
    operations: Any = None  # optional dict or object with operations_summary()
    governance: Any = None  # optional dict or object with governance_summary()
    pilot: Any = None  # optional dict or object with pilot_summary()
    latent: Any = None  # optional dict or LatentCognition (summary())
    world_model: Any = None  # optional dict or WorldModelBuilder
    homeostasis: Any = None  # optional dict or HomeostaticRegulator
    executive: Any = None  # optional dict or ExecutiveLayer (summary())
    ego: Any = None  # optional dict or SelfModel (summary())
    communication: Any = None  # optional dict or CommunicationGateway
    developmental: Any = None  # optional dict or DevelopmentalRuntime
    proto_language: Any = None  # optional dict or ProtoLanguageLayer
    ecology: Any = None  # optional dict or DevelopmentalNursery
    active_perception: Any = None  # optional dict or ActiveSensingController
    hypothesis: Any = None  # optional dict or HypothesisEngine
    autoregeneration: Any = None  # optional dict or AutoRegenerationEngine
    logos: Any = None  # optional dict or LogosComplexityEngine
    conscience: Any = None  # optional dict or ConscienceOrchestrator
    pilot1: Any = None  # optional dict/object of Pilot-1 status (observe-only)
    post_pilot: Any = None  # optional dict/object of post-pilot analysis
    sensory_membrane: Any = None  # optional dict/object of membrane status
    pilot2: Any = None  # optional dict/object of Pilot-2 read-only soak status
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
        sub = bridge.substrate
        m = sub.metrics()
        # For the ESN keep the recurrent-matrix density as "sparsity" (the
        # original meaning); other substrates report it via their extras too.
        sparsity = float(m.extras.get("connection_density", m.sparsity))
        desire = bridge.suggest_desire()
        return NeuralSubstrateState(
            reservoir_size=sub.state_size,
            reservoir_state_norm=m.state_norm,
            reservoir_sparsity=sparsity,
            input_vector_size=sub.input_size,
            readout_output_size=bridge.readout.n_outputs,
            readout_weight_norm=bridge.readout.weight_magnitude(),
            prediction_confidence=desire.confidence if desire else 0.0,
            average_prediction_error=bridge.telemetry.average_prediction_error,
            substrate_type=sub.name,
            substrate_activity_rate=m.activity_rate,
            substrate_drift=m.drift,
            spike_rate=m.spike_rate,
            silence_ratio=m.silence_ratio,
            saturation_ratio=m.saturation_ratio,
            substrate_switch_history=list(getattr(bridge, "substrate_switches", [])),
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
        sub = bridge.substrate
        m = sub.metrics()
        sub_metrics: Dict[str, Any] = {
            "size": sub.state_size,
            "state_norm": round(m.state_norm, 4),
            "activity_rate": round(m.activity_rate, 4),
        }
        if m.spike_rate is not None:
            sub_metrics["spike_rate"] = round(m.spike_rate, 4)
        if bridge.esn is not None:
            sub_metrics["spectral_radius"] = bridge.esn.achieved_spectral_radius
        return [
            ModuleState("substrate", f"{sub.name} temporal substrate", metrics=sub_metrics),
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
            max_reservoir_size=runner.bridge.substrate.state_size,
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
        state = PlasticityState(
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
        # Controlled-plasticity observations (if a runner has an engine).
        engine = getattr(self.runner, "plasticity_engine", None)
        if engine is not None:
            snap = engine.snapshot()
            state.applied_plasticity_count = snap["applied_count"]
            state.rejected_plasticity_count = snap["rejected_count"]
            state.rollback_count = snap["rollback_count"]
            state.last_applied_step = snap["last_applied"]
            state.last_rejected_step = snap["last_rejected"]
            state.mutable_parameters = snap["current_parameters"]
            state.plasticity_safety_status = snap["safety_status"]
            state.plasticity_audit_path = snap["audit_path"]
        return state

    def _unknown(self, bridge: Optional["SolarisNeuralBridge"], memory_report) -> UnknownState:
        drift = 0.0
        if bridge is not None:
            current = bridge.substrate_state_norm()
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

    @staticmethod
    def _active_perception_summary(snap: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten an ActiveSensingController snapshot for the Inner MAP."""
        policy = snap.get("policy") or {}
        attention = snap.get("attention") or {}
        salience = snap.get("salience") or {}
        uncertainty = snap.get("uncertainty") or {}
        curiosity = snap.get("curiosity") or {}
        memory = snap.get("exploration_memory") or {}
        stagnation = snap.get("stagnation") or {}
        last_decision = policy.get("last_decision") or {}
        ranked = salience.get("ranked") or []
        top_uncertain = uncertainty.get("top_targets") or []
        current_focus = attention.get("current") or {}
        return {
            "enabled": snap.get("enabled", True),
            "sampling_policy_mode": policy.get("mode"),
            "current_attention_focus": current_focus.get("target_ref"),
            "top_salience_target": (ranked[0].get("target_ref")
                                    if ranked else None),
            "top_uncertainty_target": (top_uncertain[0].get("target_ref")
                                       if top_uncertain else None),
            "curiosity_pressure": curiosity.get("pressure"),
            "latest_sampling_action": (last_decision.get("action") or {}).get(
                "action_type"),
            "latest_sampling_result": (snap.get("last_result") or {}).get(
                "outcome"),
            "useful_sampling_rate": memory.get("useful_rate"),
            "blocked_sampling_count": snap.get("blocked_count"),
            "stagnation_state": stagnation.get("status"),
            "active_perception_report_path": snap.get("report_path"),
            "authority": False,
        }

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
                max_reservoir_size=self.bridge.substrate.state_size,
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
        if self.sidecar is not None:
            # Read-only summary of the Solaris integration status.
            model.integration = self.sidecar.integration_summary()
        if self.embodiment is not None:
            # Read-only summary of the simulated body/world (simulation-only).
            model.embodiment = self.embodiment.embodiment_summary()
        if self.evaluation is not None:
            # Last-benchmark status (dict, or an object exposing a summary).
            if hasattr(self.evaluation, "evaluation_summary"):
                model.evaluation = self.evaluation.evaluation_summary()
            elif isinstance(self.evaluation, dict):
                model.evaluation = dict(self.evaluation)
        if self.operations is not None:
            # Operational supervision status (read-only).
            if hasattr(self.operations, "operations_summary"):
                model.operations = self.operations.operations_summary()
            elif isinstance(self.operations, dict):
                model.operations = dict(self.operations)
        if self.governance is not None:
            # Governance status (read-only): policy, risk, approvals, stop.
            if hasattr(self.governance, "governance_summary"):
                model.governance = self.governance.governance_summary()
            elif isinstance(self.governance, dict):
                model.governance = dict(self.governance)
        if self.pilot is not None:
            # Pilot-0 deployment status (read-only).
            if hasattr(self.pilot, "pilot_summary"):
                model.pilot = self.pilot.pilot_summary()
            elif isinstance(self.pilot, dict):
                model.pilot = dict(self.pilot)
        latent = self.latent
        if latent is None and self.runner is not None:
            latent = getattr(self.runner, "latent", None)
        if latent is not None:
            # Latent cognition status (read-only; offline processing).
            if hasattr(latent, "summary"):
                model.latent = latent.summary()
            elif isinstance(latent, dict):
                model.latent = dict(latent)
        world_model = self.world_model
        if world_model is None and self.runner is not None:
            world_model = getattr(self.runner, "world_model", None)
        if world_model is not None:
            # World model status (read-only; observed graph structure).
            if hasattr(world_model, "world_model_summary"):
                model.world_model = world_model.world_model_summary()
            elif isinstance(world_model, dict):
                model.world_model = dict(world_model)
        homeostasis = self.homeostasis
        if homeostasis is None and self.runner is not None:
            homeostasis = getattr(self.runner, "homeostasis", None)
        if homeostasis is not None:
            # Homeostasis status (read-only; pressure estimates).
            if hasattr(homeostasis, "summary"):
                model.homeostasis = homeostasis.summary()
            elif isinstance(homeostasis, dict):
                model.homeostasis = dict(homeostasis)
        executive = self.executive
        if executive is None and self.runner is not None:
            executive = getattr(self.runner, "executive", None)
        if executive is not None:
            # Executive status (read-only; arbitration evidence).
            if hasattr(executive, "summary"):
                model.executive = executive.summary()
            elif isinstance(executive, dict):
                model.executive = dict(executive)
        ego = self.ego
        if ego is None and self.runner is not None:
            ego = getattr(self.runner, "ego", None)
        if ego is not None:
            # Ego/self-model status (read-only; operational continuity).
            if hasattr(ego, "summary"):
                model.ego = ego.summary()
            elif isinstance(ego, dict):
                model.ego = dict(ego)
        communication = self.communication
        if communication is None and self.runner is not None:
            communication = getattr(self.runner, "communication", None)
        if communication is not None:
            # Communication status (read-only; interface, not authority).
            if hasattr(communication, "summary"):
                model.communication = communication.summary()
            elif isinstance(communication, dict):
                model.communication = dict(communication)
        developmental = self.developmental
        if developmental is None and self.runner is not None:
            developmental = getattr(self.runner, "developmental", None)
        if developmental is not None:
            # Developmental status (read-only; long-horizon labels).
            if hasattr(developmental, "summary"):
                model.developmental = developmental.summary()
            elif isinstance(developmental, dict):
                model.developmental = dict(developmental)
        proto_language = self.proto_language
        if proto_language is None and self.runner is not None:
            proto_language = getattr(self.runner, "protolanguage", None)
        if proto_language is None and developmental is not None:
            proto_language = getattr(developmental, "protolanguage",
                                     None)
        if proto_language is not None:
            # Proto-language status (read-only; signs, never authority).
            if hasattr(proto_language, "summary"):
                model.proto_language = proto_language.summary()
            elif isinstance(proto_language, dict):
                model.proto_language = dict(proto_language)
        ecology = self.ecology
        if ecology is None and self.runner is not None:
            ecology = getattr(self.runner, "nursery", None)
        if ecology is None and developmental is not None:
            ecology = getattr(developmental, "nursery", None)
        if ecology is not None:
            # Ecology status (read-only; a world, never authority).
            if hasattr(ecology, "summary"):
                model.ecology = ecology.summary()
            elif isinstance(ecology, dict):
                model.ecology = dict(ecology)
        active_perception = self.active_perception
        if active_perception is None and self.runner is not None:
            active_perception = getattr(self.runner, "active_perception",
                                        None)
        if active_perception is None and developmental is not None:
            active_perception = getattr(developmental, "active_perception",
                                        None)
        if active_perception is not None:
            # Active perception status (read-only; sampling regulates
            # exposure, never authority).
            if hasattr(active_perception, "snapshot"):
                snap = active_perception.snapshot()
            elif isinstance(active_perception, dict):
                snap = active_perception
            else:
                snap = {}
            if snap:
                model.active_perception = self._active_perception_summary(
                    snap)
        hypothesis = self.hypothesis
        if hypothesis is None and self.runner is not None:
            hypothesis = getattr(self.runner, "hypothesis_engine", None)
        if hypothesis is None and developmental is not None:
            hypothesis = getattr(developmental, "hypothesis_engine", None)
        if hypothesis is not None:
            # Hypothesis engine status (read-only; research artifacts, never
            # authority and never beliefs).
            if hasattr(hypothesis, "summary"):
                model.hypothesis = hypothesis.summary()
            elif isinstance(hypothesis, dict):
                model.hypothesis = dict(hypothesis)
        autoregen = self.autoregeneration
        if autoregen is None and self.runner is not None:
            autoregen = getattr(self.runner, "autoregeneration", None)
        if autoregen is None and developmental is not None:
            autoregen = getattr(developmental, "autoregeneration", None)
        if autoregen is not None:
            # Auto-regeneration status (read-only; repairs runtime state,
            # never source code, never authority).
            if hasattr(autoregen, "summary"):
                model.autoregeneration = autoregen.summary()
            elif isinstance(autoregen, dict):
                model.autoregeneration = dict(autoregen)
        logos = self.logos
        if logos is None and self.runner is not None:
            logos = getattr(self.runner, "logos", None)
        if logos is None and developmental is not None:
            logos = getattr(developmental, "logos", None)
        if logos is not None:
            # LOGOS status (read-only; a tension engine, never authority).
            if hasattr(logos, "summary"):
                model.logos = logos.summary()
            elif isinstance(logos, dict):
                model.logos = dict(logos)
        conscience = self.conscience
        if conscience is None and self.runner is not None:
            conscience = getattr(self.runner, "conscience", None)
        if conscience is not None:
            # Conscience runtime status (read-only; the orchestrator owns no
            # action authority and no module is sovereign).
            if hasattr(conscience, "summary"):
                model.conscience = conscience.summary()
            elif isinstance(conscience, dict):
                model.conscience = dict(conscience)
        pilot1 = self.pilot1
        if pilot1 is None and self.runner is not None:
            pilot1 = getattr(self.runner, "pilot1", None)
        if pilot1 is not None:
            # Pilot-1 status (read-only; a bounded software test, never
            # consciousness evidence).
            if isinstance(pilot1, dict):
                model.pilot1 = dict(pilot1)
            elif hasattr(pilot1, "pilot_status"):
                model.pilot1 = pilot1.pilot_status()
            elif hasattr(pilot1, "snapshot"):
                model.pilot1 = pilot1.snapshot()
        post_pilot = self.post_pilot
        if post_pilot is None and self.runner is not None:
            post_pilot = getattr(self.runner, "post_pilot", None)
        if post_pilot is not None:
            # Post-pilot forensic status (read-only; analyzability/operational
            # findings only, never a consciousness claim).
            if isinstance(post_pilot, dict):
                model.post_pilot = dict(post_pilot)
            elif hasattr(post_pilot, "summary"):
                model.post_pilot = post_pilot.summary()
        membrane = self.sensory_membrane
        if membrane is None and self.runner is not None:
            membrane = getattr(self.runner, "sensory_membrane", None)
        if membrane is not None:
            # Read-only sensory membrane status (read-only; environmental
            # input only, never an operator command).
            if isinstance(membrane, dict):
                model.sensory_membrane = dict(membrane)
            elif hasattr(membrane, "summary"):
                model.sensory_membrane = membrane.summary()
        pilot2 = self.pilot2
        if pilot2 is None and self.runner is not None:
            pilot2 = getattr(self.runner, "pilot2", None)
        if pilot2 is not None:
            # Pilot-2 read-only soak status (read-only; environmental exposure
            # only, never actuation; no consciousness claim).
            if isinstance(pilot2, dict):
                model.pilot2 = dict(pilot2)
            elif hasattr(pilot2, "snapshot"):
                model.pilot2 = pilot2.snapshot()
            elif hasattr(pilot2, "summary"):
                model.pilot2 = pilot2.summary()
        if self.bridge is not None and getattr(self.bridge, "enable_language_trace", False) \
                and self.bridge.meaning_trace_builder is not None:
            builder = self.bridge.meaning_trace_builder
            counts = builder.category_counts()
            dominant = sorted(counts, key=counts.get, reverse=True)[:3]
            last_atom = builder.atoms[-1].sentence() if builder.atoms else None
            report_path = getattr(self.runner, "pm", None)
            model.language = {
                "enabled": True,
                "meaning_atom_count": len(builder),
                "causal_trace_count": len(getattr(
                    getattr(self.bridge, "causal_builder", None), "traces", {}) or {}),
                "last_explanation_summary": last_atom,
                "dominant_categories": dominant,
                "unknown_statements": counts.get("unknown", 0),
                "queryable": True,
                "last_session_report_path": (
                    str(report_path.session_report_md_path)
                    if report_path is not None else None),
            }
        model.touch()
        self._model = model
        return model

    def snapshot(self) -> Dict[str, Any]:
        """Return the latest model as a dict (computing one if needed)."""
        model = self._model or self.update()
        return model.to_dict()
