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
    motor_membrane: Any = None  # optional dict/object of motor membrane status
    pilot3: Any = None  # optional dict/object of Pilot-3 soak status
    pilot4: Any = None  # optional dict/object of Pilot-4 planning status
    safety_invariants: Any = None  # optional dict/object of safety status
    research_lab: Any = None  # optional dict/object of research-lab status
    architecture_evolution: Any = None  # optional dict/object of arch status
    operator_console: Any = None  # optional dict/object of operator-console status
    plural_sensorium: Any = None  # optional dict/object of plural-sensorium status
    organismic_demo: Any = None  # optional dict/object of organismic-demo status
    live_field: Any = None  # optional dict/object of live-field status
    sensorium_lab: Any = None  # optional dict/object of sensorium-lab status
    feeder_sdk: Any = None  # optional dict/object of feeder-SDK status
    perceptual_metabolism: Any = None  # optional dict/object of metabolism status
    perceptual_ontogenesis: Any = None  # optional dict/object of ontogenesis status
    semiogenesis: Any = None  # optional dict/object of semiogenesis status
    sensorium_cognition: Any = None  # optional dict/object of cognition status
    self_boundary: Any = None  # optional dict/object of self-boundary status
    desire_formation: Any = None  # optional dict/object of desire-formation status
    action_reaction: Any = None  # optional dict/object of action-reaction status
    developmental_life: Any = None  # optional dict/object of developmental status
    developmental_soak: Any = None  # optional dict/object of soak status
    developmental_replication: Any = None  # optional dict/object of replication
    experiment_compiler: Any = None  # optional dict/object of compiler status
    implementation_intake: Any = None  # optional dict/object of intake status
    post_merge_assimilation: Any = None  # optional dict/object of post-merge
    research_baseline: Any = None  # optional dict/object of research baseline
    research_cycle: Any = None  # optional dict/object of research-cycle status
    scientific_claims: Any = None  # optional dict/object of scientific-claims
    independent_review: Any = None  # optional dict/object of independent-review
    review_assimilation: Any = None  # optional dict/object of review-assimilation
    alpha_system: Any = None  # optional dict/object of alpha-system status
    architecture_book: Any = None  # optional dict/object of documentation status
    live_birth: Any = None  # optional dict/object of live read-only birth status
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
        motor = self.motor_membrane
        if motor is None and self.runner is not None:
            motor = getattr(self.runner, "motor_membrane", None)
        if motor is not None:
            # Motor membrane status (read-only view; simulation/dry-run only,
            # real_world_authority=false; no agency/consciousness claim).
            if isinstance(motor, dict):
                model.motor_membrane = dict(motor)
            elif hasattr(motor, "summary"):
                model.motor_membrane = motor.summary()
        pilot3 = self.pilot3
        if pilot3 is None and self.runner is not None:
            pilot3 = getattr(self.runner, "pilot3", None)
        if pilot3 is not None:
            # Pilot-3 simulated embodiment soak status (read-only view;
            # simulation/dry-run only; real_world_authority=false).
            if isinstance(pilot3, dict):
                model.pilot3 = dict(pilot3)
            elif hasattr(pilot3, "pilot3_status"):
                model.pilot3 = pilot3.pilot3_status()
            elif hasattr(pilot3, "snapshot"):
                model.pilot3 = pilot3.snapshot()
        pilot4 = self.pilot4
        if pilot4 is None and self.runner is not None:
            pilot4 = getattr(self.runner, "pilot4", None)
        if pilot4 is not None:
            # Pilot-4 planning-only readiness status (read-only view; planning
            # only; real_world_actuation_enabled=false).
            if isinstance(pilot4, dict):
                model.pilot4 = dict(pilot4)
            elif hasattr(pilot4, "pilot4_status"):
                model.pilot4 = pilot4.pilot4_status()
            elif hasattr(pilot4, "snapshot"):
                model.pilot4 = pilot4.snapshot()
        safety = self.safety_invariants
        if safety is None and self.runner is not None:
            safety = getattr(self.runner, "safety_invariants", None)
        if safety is not None:
            # System-wide safety invariant status (read-only view; the safety
            # layer runs no actions and hides no critical failure).
            if isinstance(safety, dict):
                model.safety_invariants = dict(safety)
            elif hasattr(safety, "safety_invariant_status"):
                model.safety_invariants = safety.safety_invariant_status()
            elif hasattr(safety, "snapshot"):
                model.safety_invariants = safety.snapshot()
        research = self.research_lab
        if research is None and self.runner is not None:
            research = getattr(self.runner, "research_lab", None)
        if research is not None:
            # Research-lab status (read-only view; bounded measurement only).
            if isinstance(research, dict):
                model.research_lab = dict(research)
            elif hasattr(research, "research_lab_status"):
                model.research_lab = research.research_lab_status()
            elif hasattr(research, "snapshot"):
                model.research_lab = research.snapshot()
        arch = self.architecture_evolution
        if arch is None and self.runner is not None:
            arch = getattr(self.runner, "architecture_evolution", None)
        if arch is not None:
            # Architecture-evolution status (read-only view; planning only).
            if isinstance(arch, dict):
                model.architecture_evolution = dict(arch)
            elif hasattr(arch, "architecture_status"):
                model.architecture_evolution = arch.architecture_status()
            elif hasattr(arch, "snapshot"):
                model.architecture_evolution = arch.snapshot()
        console = self.operator_console
        if console is None and self.runner is not None:
            console = getattr(self.runner, "operator_console", None)
        if console is not None:
            # Operator-console status (read-only view; local coordinator only).
            if isinstance(console, dict):
                model.operator_console = dict(console)
            elif hasattr(console, "operator_console_status"):
                model.operator_console = console.operator_console_status()
            elif hasattr(console, "snapshot"):
                model.operator_console = console.snapshot()
        sensorium = self.plural_sensorium
        if sensorium is None and self.runner is not None:
            sensorium = getattr(self.runner, "plural_sensorium", None)
        if sensorium is not None:
            # Plural-sensorium status (read-only organismic perception view).
            if isinstance(sensorium, dict):
                model.plural_sensorium = dict(sensorium)
            elif hasattr(sensorium, "plural_sensorium_status"):
                model.plural_sensorium = sensorium.plural_sensorium_status()
            elif hasattr(sensorium, "snapshot"):
                model.plural_sensorium = sensorium.snapshot()
        demo = self.organismic_demo
        if demo is None and self.runner is not None:
            demo = getattr(self.runner, "organismic_demo", None)
        if demo is not None:
            # Minimal-field-organism demo status (read-only observation view).
            if isinstance(demo, dict):
                model.organismic_demo = dict(demo)
            elif hasattr(demo, "demo_status"):
                model.organismic_demo = demo.demo_status()
            elif hasattr(demo, "snapshot"):
                model.organismic_demo = demo.snapshot()
        live = self.live_field
        if live is None and self.runner is not None:
            live = getattr(self.runner, "live_field", None)
        if live is not None:
            # Live-field status (read-only real-feeder integration view).
            if isinstance(live, dict):
                model.live_field = dict(live)
            elif hasattr(live, "live_field_status"):
                model.live_field = live.live_field_status()
            elif hasattr(live, "snapshot"):
                model.live_field = live.snapshot()
        lab = self.sensorium_lab
        if lab is None and self.runner is not None:
            lab = getattr(self.runner, "sensorium_lab", None)
        if lab is not None:
            # Sensorium-lab status (structural differentiation study view).
            if isinstance(lab, dict):
                model.sensorium_lab = dict(lab)
            elif hasattr(lab, "sensorium_lab_status"):
                model.sensorium_lab = lab.sensorium_lab_status()
            elif hasattr(lab, "snapshot"):
                model.sensorium_lab = lab.snapshot()
        feeder = self.feeder_sdk
        if feeder is None and self.runner is not None:
            feeder = getattr(self.runner, "feeder_sdk", None)
        if feeder is not None:
            # Feeder-SDK status (read-only sensory-organ boundary view).
            if isinstance(feeder, dict):
                model.feeder_sdk = dict(feeder)
            elif hasattr(feeder, "feeder_sdk_status"):
                model.feeder_sdk = feeder.feeder_sdk_status()
            elif hasattr(feeder, "snapshot"):
                model.feeder_sdk = feeder.snapshot()
        metabolism = self.perceptual_metabolism
        if metabolism is None and self.runner is not None:
            metabolism = getattr(self.runner, "perceptual_metabolism", None)
        if metabolism is not None:
            # Perceptual-metabolism status (internal regulation view).
            if isinstance(metabolism, dict):
                model.perceptual_metabolism = dict(metabolism)
            elif hasattr(metabolism, "metabolism_status"):
                model.perceptual_metabolism = metabolism.metabolism_status()
            elif hasattr(metabolism, "snapshot"):
                model.perceptual_metabolism = metabolism.snapshot()
        ontogenesis = self.perceptual_ontogenesis
        if ontogenesis is None and self.runner is not None:
            ontogenesis = getattr(self.runner, "perceptual_ontogenesis", None)
        if ontogenesis is not None:
            # Perceptual-ontogenesis status (internal world-formation view).
            if isinstance(ontogenesis, dict):
                model.perceptual_ontogenesis = dict(ontogenesis)
            elif hasattr(ontogenesis, "ontogenesis_status"):
                model.perceptual_ontogenesis = ontogenesis.ontogenesis_status()
            elif hasattr(ontogenesis, "snapshot"):
                model.perceptual_ontogenesis = ontogenesis.snapshot()
        semiogenesis = self.semiogenesis
        if semiogenesis is None and self.runner is not None:
            semiogenesis = getattr(self.runner, "semiogenesis", None)
        if semiogenesis is not None:
            # Semiogenesis status (internal sign-formation view).
            if isinstance(semiogenesis, dict):
                model.semiogenesis = dict(semiogenesis)
            elif hasattr(semiogenesis, "semiogenesis_status"):
                model.semiogenesis = semiogenesis.semiogenesis_status()
            elif hasattr(semiogenesis, "snapshot"):
                model.semiogenesis = semiogenesis.snapshot()
        cognition = self.sensorium_cognition
        if cognition is None and self.runner is not None:
            cognition = getattr(self.runner, "sensorium_cognition", None)
        if cognition is not None:
            # Sensorium-cognition status (sign-based thought view).
            if isinstance(cognition, dict):
                model.sensorium_cognition = dict(cognition)
            elif hasattr(cognition, "cognition_status"):
                model.sensorium_cognition = cognition.cognition_status()
            elif hasattr(cognition, "snapshot"):
                model.sensorium_cognition = cognition.snapshot()
        self_boundary = self.self_boundary
        if self_boundary is None and self.runner is not None:
            self_boundary = getattr(self.runner, "self_boundary", None)
        if self_boundary is not None:
            # Self-boundary status (operational self/world boundary view).
            if isinstance(self_boundary, dict):
                model.self_boundary = dict(self_boundary)
            elif hasattr(self_boundary, "self_boundary_status"):
                model.self_boundary = self_boundary.self_boundary_status()
            elif hasattr(self_boundary, "snapshot"):
                model.self_boundary = self_boundary.snapshot()
        desire = self.desire_formation
        if desire is None and self.runner is not None:
            desire = getattr(self.runner, "desire_formation", None)
        if desire is not None:
            # Desire-formation status (operational desire/motivation view).
            if isinstance(desire, dict):
                model.desire_formation = dict(desire)
            elif hasattr(desire, "desire_status"):
                model.desire_formation = desire.desire_status()
            elif hasattr(desire, "snapshot"):
                model.desire_formation = desire.snapshot()
        action_reaction = self.action_reaction
        if action_reaction is None and self.runner is not None:
            action_reaction = getattr(self.runner, "action_reaction", None)
        if action_reaction is not None:
            # Action-reaction status (closed-loop view).
            if isinstance(action_reaction, dict):
                model.action_reaction = dict(action_reaction)
            elif hasattr(action_reaction, "action_reaction_status"):
                model.action_reaction = \
                    action_reaction.action_reaction_status()
            elif hasattr(action_reaction, "snapshot"):
                model.action_reaction = action_reaction.snapshot()
        developmental = self.developmental_life
        if developmental is None and self.runner is not None:
            developmental = getattr(self.runner, "developmental_life", None)
        if developmental is not None:
            # Developmental-life status (long-horizon structural change view).
            if isinstance(developmental, dict):
                model.developmental_life = dict(developmental)
            elif hasattr(developmental, "developmental_status"):
                model.developmental_life = developmental.developmental_status()
            elif hasattr(developmental, "snapshot"):
                model.developmental_life = developmental.snapshot()
        soak = self.developmental_soak
        if soak is None and self.runner is not None:
            soak = getattr(self.runner, "developmental_soak", None)
        if soak is not None:
            # Developmental-soak status (month-scale study-protocol view).
            if isinstance(soak, dict):
                model.developmental_soak = dict(soak)
            elif hasattr(soak, "soak_status"):
                model.developmental_soak = soak.soak_status()
            elif hasattr(soak, "snapshot"):
                model.developmental_soak = soak.snapshot()
        replication = self.developmental_replication
        if replication is None and self.runner is not None:
            replication = getattr(self.runner, "developmental_replication", None)
        if replication is not None:
            # Developmental-replication status (cross-run comparison view).
            if isinstance(replication, dict):
                model.developmental_replication = dict(replication)
            elif hasattr(replication, "replication_status"):
                model.developmental_replication = \
                    replication.replication_status()
            elif hasattr(replication, "snapshot"):
                model.developmental_replication = replication.snapshot()
        compiler = self.experiment_compiler
        if compiler is None and self.runner is not None:
            compiler = getattr(self.runner, "experiment_compiler", None)
        if compiler is not None:
            # Experiment-compiler status (evidence -> implementation docs view).
            if isinstance(compiler, dict):
                model.experiment_compiler = dict(compiler)
            elif hasattr(compiler, "compiler_status"):
                model.experiment_compiler = compiler.compiler_status()
            elif hasattr(compiler, "snapshot"):
                model.experiment_compiler = compiler.snapshot()
        intake = self.implementation_intake
        if intake is None and self.runner is not None:
            intake = getattr(self.runner, "implementation_intake", None)
        if intake is not None:
            # Implementation-intake status (evidence-auditor view).
            if isinstance(intake, dict):
                model.implementation_intake = dict(intake)
            elif hasattr(intake, "intake_status"):
                model.implementation_intake = intake.intake_status()
            elif hasattr(intake, "snapshot"):
                model.implementation_intake = intake.snapshot()
        post_merge = self.post_merge_assimilation
        if post_merge is None and self.runner is not None:
            post_merge = getattr(self.runner, "post_merge_assimilation", None)
        if post_merge is not None:
            # Post-merge-assimilation status (research-ledger view).
            if isinstance(post_merge, dict):
                model.post_merge_assimilation = dict(post_merge)
            elif hasattr(post_merge, "post_merge_status"):
                model.post_merge_assimilation = post_merge.post_merge_status()
            elif hasattr(post_merge, "snapshot"):
                model.post_merge_assimilation = post_merge.snapshot()
        baseline = self.research_baseline
        if baseline is None and self.runner is not None:
            baseline = getattr(self.runner, "research_baseline", None)
        if baseline is not None:
            # Research-baseline status (versioned reproducible-snapshot view).
            if isinstance(baseline, dict):
                model.research_baseline = dict(baseline)
            elif hasattr(baseline, "research_baseline_status"):
                model.research_baseline = baseline.research_baseline_status()
            elif hasattr(baseline, "snapshot_view"):
                model.research_baseline = baseline.snapshot_view()
        cycle = self.research_cycle
        if cycle is None and self.runner is not None:
            cycle = getattr(self.runner, "research_cycle", None)
        if cycle is not None:
            # Research-cycle status (closed-cycle tracking view).
            if isinstance(cycle, dict):
                model.research_cycle = dict(cycle)
            elif hasattr(cycle, "research_cycle_status"):
                model.research_cycle = cycle.research_cycle_status()
            elif hasattr(cycle, "snapshot"):
                model.research_cycle = cycle.snapshot()
        claims = self.scientific_claims
        if claims is None and self.runner is not None:
            claims = getattr(self.runner, "scientific_claims", None)
        if claims is not None:
            # Scientific-claims status (evidence-to-claim discipline view).
            if isinstance(claims, dict):
                model.scientific_claims = dict(claims)
            elif hasattr(claims, "scientific_claims_status"):
                model.scientific_claims = claims.scientific_claims_status()
            elif hasattr(claims, "snapshot"):
                model.scientific_claims = claims.snapshot()
        review = self.independent_review
        if review is None and self.runner is not None:
            review = getattr(self.runner, "independent_review", None)
        if review is not None:
            # Independent-review status (local offline review-prep view).
            if isinstance(review, dict):
                model.independent_review = dict(review)
            elif hasattr(review, "independent_review_status"):
                model.independent_review = review.independent_review_status()
            elif hasattr(review, "snapshot"):
                model.independent_review = review.snapshot()
        assimilation = self.review_assimilation
        if assimilation is None and self.runner is not None:
            assimilation = getattr(self.runner, "review_assimilation", None)
        if assimilation is not None:
            # Review-assimilation status (reviewer feedback as research evidence).
            if isinstance(assimilation, dict):
                model.review_assimilation = dict(assimilation)
            elif hasattr(assimilation, "review_assimilation_status"):
                model.review_assimilation = \
                    assimilation.review_assimilation_status()
            elif hasattr(assimilation, "snapshot"):
                model.review_assimilation = assimilation.snapshot()
        alpha = self.alpha_system
        if alpha is None and self.runner is not None:
            alpha = getattr(self.runner, "alpha_system", None)
        if alpha is not None:
            # Alpha-system status (unified local assembly view).
            if isinstance(alpha, dict):
                model.alpha_system = dict(alpha)
            elif hasattr(alpha, "alpha_status"):
                model.alpha_system = alpha.alpha_status()
            elif hasattr(alpha, "snapshot"):
                model.alpha_system = alpha.snapshot()
        book = self.architecture_book
        if book is None and self.runner is not None:
            book = getattr(self.runner, "architecture_book", None)
        if book is not None:
            # Documentation-build status (whitepaper / architecture book view).
            if isinstance(book, dict):
                model.architecture_book = dict(book)
            elif hasattr(book, "documentation_status"):
                model.architecture_book = book.documentation_status()
            elif hasattr(book, "snapshot"):
                model.architecture_book = book.snapshot()
        birth = self.live_birth
        if birth is None and self.runner is not None:
            birth = getattr(self.runner, "live_birth", None)
        if birth is not None:
            # Live read-only birth status (bounded first environmental contact).
            if isinstance(birth, dict):
                model.live_birth = dict(birth)
            elif hasattr(birth, "live_birth_status"):
                model.live_birth = birth.live_birth_status()
            elif hasattr(birth, "snapshot"):
                model.live_birth = birth.snapshot()
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
