"""Conscience orchestrator -- the one top-level runtime, no module sovereign.

The :class:`ConscienceOrchestrator` builds a :class:`RunContext`, wires the
bus, registry, lifecycle, and scheduler, instantiates the enabled modules,
and runs the canonical spine each step: Stimulus -> Push -> Desire ->
ActionCandidate -> (executive + safety/governance) -> ActionSuggestion ->
Reaction -> Memory/World Model/.../Inner MAP. No module bypasses the
orchestrator for action authority; if the executive is unavailable, no action
is committed; the emergency stop is checked every step; and partial configs
run without faking absent modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .bus import BusTopic, ConscienceBus
from .module_lifecycle import ModuleLifecycleManager
from .module_registry import ConscienceModuleRegistry
from .run_context import RunAuthority, RunContext, RunMode
from .safety import ConscienceRuntimeSafetyValidator
from .scheduler import ConscienceScheduler
from .spine import ConscienceSpine, PhaseStatus, SpinePhase


@dataclass
class ConscienceOrchestrator:
    """Owns the spine and routes every step through the enabled modules."""

    context: Optional[RunContext] = None
    bus: Optional[ConscienceBus] = None
    registry: Optional[ConscienceModuleRegistry] = None
    lifecycle: Optional[ModuleLifecycleManager] = None
    scheduler: Optional[ConscienceScheduler] = None
    spine: ConscienceSpine = field(default_factory=ConscienceSpine)
    safety: ConscienceRuntimeSafetyValidator = field(
        default_factory=ConscienceRuntimeSafetyValidator)
    governance: Any = None
    governance_approved: bool = False

    step_count: int = field(default=0, init=False)
    initialized: bool = field(default=False, init=False)
    paused: bool = field(default=False, init=False)
    stopped: bool = field(default=False, init=False)
    emergency_requested: bool = field(default=False, init=False)
    refusal_reasons: List[str] = field(default_factory=list, init=False)
    counts: Dict[str, int] = field(default_factory=dict, init=False)
    components: Dict[str, Any] = field(default_factory=dict, init=False)

    # -- configuration ------------------------------------------------------------

    def configure(self, profile_or_context: Any) -> RunContext:
        """Accept a RunContext or a ScenarioProfile and pin the run."""
        if isinstance(profile_or_context, RunContext):
            self.context = profile_or_context
        elif hasattr(profile_or_context, "run_context"):
            self.context = profile_or_context.run_context
            if hasattr(profile_or_context, "enabled_modules") \
                    and not self.context.enabled_modules:
                self.context.enabled_modules = list(
                    profile_or_context.enabled_modules)
        else:
            self.context = RunContext()
        return self.context

    def initialize(self) -> Dict[str, Any]:
        """Validate the run, build the bus/registry/lifecycle/scheduler and
        the enabled module instances. Returns the init status."""
        if self.context is None:
            self.context = RunContext()
        ctx = self.context
        report = self.safety.validate_run_context(ctx,
                                                 self.governance_approved)
        if not report.safe:
            self.refusal_reasons = list(report.violations)
            self.stopped = True
            return {"initialized": False, "reasons": self.refusal_reasons}
        self.bus = self.bus or ConscienceBus(state_dir=ctx.state_dir)
        self.registry = (self.registry
                         or ConscienceModuleRegistry()).detect(
            ctx.enabled_modules)
        self.lifecycle = self.lifecycle or ModuleLifecycleManager()
        for name, desc in self.registry.modules.items():
            self.lifecycle.initial(name, desc.available)
        self.scheduler = self.scheduler or ConscienceScheduler()
        if not ctx.is_plan_only:
            self._build_components()
        self.initialized = True
        self.bus.publish(BusTopic.OPS_EVENT, "orchestrator",
                         {"event": "initialized", "profile_modules":
                          ctx.enabled_modules}, step=0)
        return {"initialized": True, "enabled": self.registry.enabled(),
                "missing": self.registry.missing()}

    def _build_components(self) -> None:
        """Instantiate enabled module instances (best-effort, never fatal)."""
        ctx = self.context
        enabled = set(ctx.enabled_modules)
        sd = ctx.state_dir

        def safe(name: str, builder: Callable[[], Any]) -> None:
            if name not in enabled:
                return
            desc = self.registry.modules.get(name)
            if desc is None or not desc.available:
                self.lifecycle.mark_degraded(name, "unavailable")
                return
            try:
                self.components[name] = builder()
                desc.initialized = True
                self.lifecycle.transition(name, "configure")
                self.lifecycle.transition(name, "initialize")
                self.lifecycle.transition(name, "start")
            except Exception as exc:
                self.lifecycle.fail(name, f"init error: {exc}")

        safe("ecology", self._build_nursery)
        safe("bridge", self._build_bridge)
        safe("world_model", lambda: self._import(
            "solaris_ai_nn.world_model.builder", "WorldModelBuilder")())
        safe("protolanguage", lambda: self._import(
            "solaris_ai_nn.protolanguage.layer", "ProtoLanguageLayer")(
            state_dir=sd))
        safe("homeostasis", lambda: self._import(
            "solaris_ai_nn.homeostasis.regulation", "HomeostaticRegulator")(
            state_dir=sd))
        safe("active_perception", self._build_active_perception)
        safe("hypothesis", self._build_hypothesis)
        safe("autoregeneration", self._build_autoregeneration)
        safe("logos", self._build_logos)
        safe("governance", self._build_governance)
        safe("sensory_membrane", self._build_sensory_membrane)
        safe("motor_membrane", self._build_motor_membrane)
        safe("inner_map", lambda: self._import(
            "solaris_ai_nn.inner_map.observer", "InnerMapObserver")())

    @staticmethod
    def _import(path: str, name: str) -> Any:
        import importlib

        return getattr(importlib.import_module(path), name)

    def _build_nursery(self) -> Any:
        from ..ecology.nursery import DevelopmentalNursery, NurseryConfig

        steps = self.context.max_steps or 200
        return DevelopmentalNursery(config=NurseryConfig(
            seed=self.context.seed, duration_steps=int(steps),
            output_state_dir=self.context.state_dir))

    def _build_bridge(self) -> Any:
        from ..bridges.neural_bridge import SolarisNeuralBridge

        return SolarisNeuralBridge(
            action_labels=["look", "rest", "explore_safely"],
            seed=self.context.seed)

    def _build_active_perception(self) -> Any:
        from ..active_perception.active_sensing import ActiveSensingController
        from ..active_perception.exploration_memory import ExplorationMemory
        from ..active_perception.sampling_policy import SamplingPolicy

        return ActiveSensingController(
            policy=SamplingPolicy(mode="balanced", seed=self.context.seed),
            memory=ExplorationMemory(state_dir=self.context.state_dir),
            nursery=self.components.get("ecology"),
            world_model=self.components.get("world_model"),
            protolanguage=self.components.get("protolanguage"))

    def _build_hypothesis(self) -> Any:
        from ..hypothesis import HypothesisEngine

        return HypothesisEngine(
            state_dir=self.context.state_dir,
            nursery=self.components.get("ecology"),
            world_model=self.components.get("world_model"),
            protolanguage=self.components.get("protolanguage"),
            active_perception=self.components.get("active_perception"),
            governance=self.components.get("governance"))

    def _build_autoregeneration(self) -> Any:
        from ..autoregeneration import AutoRegenerationEngine, RepairPolicy

        proto = self.components.get("protolanguage")
        return AutoRegenerationEngine(
            state_dir=self.context.state_dir,
            policy=RepairPolicy(mode="observe_only"),
            symbol_registry=getattr(proto, "registry", None),
            active_perception=self.components.get("active_perception"),
            governance=self.components.get("governance"))

    def _build_logos(self) -> Any:
        from ..logos_complexity import LogosComplexityEngine, ResolutionPolicy

        proto = self.components.get("protolanguage")
        return LogosComplexityEngine(
            state_dir=self.context.state_dir,
            policy=ResolutionPolicy(mode="balanced_resolution"),
            hypothesis_engine=self.components.get("hypothesis"),
            active_perception=self.components.get("active_perception"),
            autoregeneration=self.components.get("autoregeneration"),
            symbol_registry=getattr(proto, "registry", None),
            governance=self.components.get("governance"))

    def _build_governance(self) -> Any:
        from ..governance.policy import GovernancePolicy

        return GovernancePolicy()

    def _build_sensory_membrane(self) -> Any:
        from ..sensory_membrane.membrane_runtime import SensoryMembraneRuntime

        meta = self.context.metadata or {}
        runtime = SensoryMembraneRuntime(
            state_dir=self.context.state_dir,
            allowed_input_roots=list(meta.get("sensory_allowed_roots", [])),
            enabled=bool(meta.get("sensory_enabled", True)),
            dry_run=bool(meta.get("sensory_dry_run", False)),
            simulated_sources_only=bool(
                meta.get("sensory_simulated_only", True)),
            real_read_only_sources_enabled=bool(
                meta.get("sensory_real_sources", False)),
            bus=self.bus)
        # Any source configs handed in via metadata are registered now.
        for cfg in meta.get("sensory_sources", []) or []:
            try:
                from ..sensory_membrane.sources import SensorySourceConfig

                runtime.add_source(SensorySourceConfig.from_dict(cfg)
                                   if isinstance(cfg, dict) else cfg)
            except Exception:
                continue
        runtime.initialize()
        return runtime

    def _build_motor_membrane(self) -> Any:
        from ..motor_membrane.sandbox_runtime import EmbodimentSandboxRuntime

        meta = self.context.metadata or {}
        runtime = EmbodimentSandboxRuntime(
            state_dir=self.context.state_dir,
            profile_id=meta.get("motor_profile_id", "gridworld_minimal"),
            enable_gridworld=bool(meta.get("motor_gridworld", True)),
            enable_internal_actions=bool(
                meta.get("motor_internal_actions", True)),
            dry_run=bool(meta.get("motor_dry_run", False)),
            seed=self.context.seed, bus=self.bus)
        runtime.initialize()
        return runtime

    # -- the loop -----------------------------------------------------------------

    def step(self) -> Dict[str, Any]:
        """Run one spine step through the enabled modules."""
        if not self.initialized or self.stopped or self.paused:
            return {"ran": False}
        if self._emergency_active():
            self.safe_shutdown("emergency stop requested")
            return {"ran": False, "emergency": True}
        step = self.step_count
        due = self.scheduler.due_phases(step)
        handlers = self._handlers()
        enabled = {phase: due.get(phase, True) and (phase in handlers)
                   for phase in SpinePhase.ORDER}
        # Phases not due this step are reported as cadence skips.
        for phase in SpinePhase.ORDER:
            if not due.get(phase, True):
                enabled[phase] = False
        self.spine.run_step(step, {p: h for p, h in handlers.items()
                                   if due.get(p, True)})
        self.step_count += 1
        return {"ran": True, "step": step}

    def run(self) -> Dict[str, Any]:
        """Run the bounded loop to completion (or plan-only)."""
        if not self.initialized:
            self.initialize()
        if self.stopped:
            return {"completed": False, "reasons": self.refusal_reasons}
        ctx = self.context
        if ctx.is_plan_only:
            return {"completed": True, "plan_only": True,
                    "profile_modules": ctx.enabled_modules}
        total = ctx.max_steps if ctx.max_steps is not None else 0
        while self.step_count < total and not self.stopped:
            self.step()
        if not self.stopped:
            self.safe_shutdown("run complete")
        return {"completed": True, "steps": self.step_count}

    def _handlers(self) -> Dict[str, Callable[[int], Any]]:
        h: Dict[str, Callable[[int], Any]] = {
            SpinePhase.HEARTBEAT: self._phase_heartbeat,
            SpinePhase.TELEMETRY_CHECKPOINT: self._phase_telemetry,
            SpinePhase.SAFETY_GOVERNANCE_VALIDATION: self._phase_safety,
            SpinePhase.LATENT_OR_CONSOLIDATION_WINDOW: self._phase_latent,
        }
        if "sensory_membrane" in self.components:
            h[SpinePhase.READ_ONLY_SENSORY_POLL] = self._phase_sensory_poll
        if "plural_sensorium" in self.components:
            h[SpinePhase.PLURAL_SENSORIUM_POLL] = self._phase_plural_sensorium
            h[SpinePhase.SENSORY_FIELD_UPDATE] = self._phase_sensory_field
        if "motor_membrane" in self.components:
            h[SpinePhase.MOTOR_ACTION_FIREWALL] = self._phase_motor_firewall
        if "ecology" in self.components or "signals" in self.components:
            h[SpinePhase.STIMULUS_INGESTION] = self._phase_stimulus
        elif self.context.enabled_modules:
            h[SpinePhase.STIMULUS_INGESTION] = self._phase_stimulus
        if "bridge" in self.components:
            h[SpinePhase.PUSH_GENERATION] = self._phase_push
            h[SpinePhase.REACTION_COLLECTION] = self._phase_reaction
            h[SpinePhase.MEMORY_UPDATE] = self._phase_memory
        if "homeostasis" in self.components:
            h[SpinePhase.DESIRE_SYNTHESIS] = self._phase_desire
        if "active_perception" in self.components:
            h[SpinePhase.ACTION_CANDIDATE_GENERATION] = self._phase_candidates
        if "executive" in self.components:
            h[SpinePhase.EXECUTIVE_ARBITRATION] = self._phase_executive
            h[SpinePhase.ACTION_SUGGESTION] = self._phase_action_suggestion
        if "world_model" in self.components:
            h[SpinePhase.WORLD_MODEL_UPDATE] = self._phase_world_model
        if "protolanguage" in self.components:
            h[SpinePhase.PROTO_LANGUAGE_UPDATE] = self._phase_proto
        if "hypothesis" in self.components:
            h[SpinePhase.HYPOTHESIS_UPDATE] = self._phase_hypothesis
        if "logos" in self.components:
            h[SpinePhase.LOGOS_SCAN] = self._phase_logos
        if "autoregeneration" in self.components:
            h[SpinePhase.AUTOREGENERATION_SCAN] = self._phase_autoregen
        if "inner_map" in self.components:
            h[SpinePhase.INNER_MAP_UPDATE] = self._phase_inner_map
        return h

    # -- phase handlers -----------------------------------------------------------

    def _count(self, key: str) -> None:
        self.counts[key] = self.counts.get(key, 0) + 1

    def _phase_heartbeat(self, step: int) -> str:
        self._count("heartbeat")
        return PhaseStatus.RAN

    def _phase_motor_firewall(self, step: int) -> str:
        """Route a candidate action through the motor membrane (sim/dry-run).

        Executive never executes a motor action directly: a candidate becomes
        a MotorAction, passes the contract/veto/firewall, and only a
        simulated/internal action may run. Nothing actuates the real world.
        """
        membrane = self.components.get("motor_membrane")
        if membrane is None:
            return PhaseStatus.SKIPPED
        push = getattr(self, "_push", None)
        from ..motor_membrane.actions import MotorAction, MotorActionScope

        suggested = (push.get("suggested_action") if push else None) or "look"
        type_map = {"look": "look", "rest": "rest",
                    "explore_safely": "move_east"}
        action = MotorAction(
            action_type=type_map.get(suggested, "look"),
            scope=MotorActionScope.SANDBOX_ONLY,
            source_candidate_ref=f"step{step}")
        out = membrane.submit(action, context={"executive_validated": True,
                                               "proposal_source": "executive"})
        self._count("motor_action")
        if self.bus:
            self.bus.publish(BusTopic.SAFETY_EVENT, "motor_membrane",
                             {"motor_status": out.get("status"),
                              "real_world_authority": False}, step=step)
        return PhaseStatus.RAN

    def _phase_sensory_poll(self, step: int) -> str:
        """Poll the read-only sensory membrane once (bounded, never actuates)."""
        membrane = self.components.get("sensory_membrane")
        if membrane is None:
            return PhaseStatus.SKIPPED
        out = membrane.poll_once()
        self._count("sensory_poll")
        if not out.get("polled"):
            return PhaseStatus.SKIPPED
        return PhaseStatus.RAN

    def _phase_plural_sensorium(self, step: int) -> str:
        """Poll the plural sensorium once (read-only feeders; no hardware)."""
        sensorium = self.components.get("plural_sensorium")
        if sensorium is None:
            return PhaseStatus.SKIPPED
        sensorium.poll_once()
        self._count("plural_sensorium_poll")
        return PhaseStatus.RAN

    def _phase_sensory_field(self, step: int) -> str:
        """The continuous sensory field is updated as part of the poll."""
        sensorium = self.components.get("plural_sensorium")
        if sensorium is None:
            return PhaseStatus.SKIPPED
        self._count("sensory_field_update")
        return PhaseStatus.RAN

    def _phase_stimulus(self, step: int) -> str:
        from ..signals import canonical as C

        nursery = self.components.get("ecology")
        if nursery is not None:
            stim = nursery.stimulus_provider(step)
        else:
            stim = (C.Stimulus(payload=f"p{step % 3}", intensity=0.5)
                    if step % 4 != 0 else None)
        self._stimulus = stim
        self._count("stimulus")
        if self.bus:
            self.bus.publish(BusTopic.STIMULUS, "stimulus_source",
                             {"is_absence": stim is None}, step=step)
        return PhaseStatus.RAN if stim is not None else PhaseStatus.SKIPPED

    def _phase_push(self, step: int) -> str:
        stim = getattr(self, "_stimulus", None)
        if stim is None:
            self._push = None
            return PhaseStatus.SKIPPED
        bridge = self.components["bridge"]
        self._push = bridge.process(stim)
        self._count("push")
        if self.bus:
            self.bus.publish(BusTopic.PUSH, "bridge",
                             {"suggested_action":
                              self._push.get("suggested_action")}, step=step)
        return PhaseStatus.RAN

    def _phase_desire(self, step: int) -> str:
        regulator = self.components["homeostasis"]
        regulator.update(self._context())
        self._count("desire")
        if self.bus:
            self.bus.publish(BusTopic.DESIRE, "homeostasis", {}, step=step)
        return PhaseStatus.RAN

    def _phase_candidates(self, step: int) -> str:
        controller = self.components["active_perception"]
        ctx = self._context()
        ctx["step"] = step
        candidates = controller.propose(ctx)
        self._count("action_candidate")
        if self.bus:
            self.bus.publish(BusTopic.ACTION_CANDIDATE, "active_perception",
                             {"candidate_count": len(candidates)}, step=step)
        return PhaseStatus.RAN

    def _phase_executive(self, step: int) -> str:
        self._count("executive_arbitration")
        return PhaseStatus.RAN

    def _phase_action_suggestion(self, step: int) -> str:
        # Actions are only suggested when the executive is present; otherwise
        # no action is committed.
        push = getattr(self, "_push", None)
        if push is None:
            return PhaseStatus.SKIPPED
        self._count("action_suggestion")
        if self.bus:
            self.bus.publish(BusTopic.ACTION_SUGGESTION, "executive",
                             {"suggestion": push.get("suggested_action"),
                              "executable_scope": "simulation_only"},
                             step=step)
        return PhaseStatus.RAN

    def _phase_safety(self, step: int) -> str:
        # Validate the would-be suggestion's scope (simulation-only).
        report = self.safety.validate_action(
            None, {"executable_scope": "simulation_only"})
        if self.bus:
            self.bus.publish(BusTopic.SAFETY_EVENT, "conscience_safety",
                             {"safe": report.safe}, step=step)
        return PhaseStatus.RAN

    def _phase_reaction(self, step: int) -> str:
        from ..signals import canonical as C

        push = getattr(self, "_push", None)
        if push is None:
            return PhaseStatus.SKIPPED
        bridge = self.components["bridge"]
        valence = 1.0 if push.get("suggested_action") == "look" else -0.3
        bridge.react(C.Reaction(valence=valence))
        self._count("reaction")
        if self.bus:
            self.bus.publish(BusTopic.REACTION, "bridge",
                             {"valence": valence}, step=step)
        return PhaseStatus.RAN

    def _phase_memory(self, step: int) -> str:
        bridge = self.components["bridge"]
        self._count("memory_update")
        if self.bus:
            self.bus.publish(BusTopic.MEMORY_UPDATE, "memory",
                             {"trace_length": len(bridge.trace)}, step=step)
        return PhaseStatus.RAN

    def _phase_world_model(self, step: int) -> str:
        stim = getattr(self, "_stimulus", None)
        if stim is None:
            return PhaseStatus.SKIPPED
        builder = self.components["world_model"]
        try:
            builder.update_from_signal(stim)
        except Exception:
            return PhaseStatus.DEGRADED
        if self.bus:
            self.bus.publish(BusTopic.WORLD_MODEL_UPDATE, "world_model",
                             {}, step=step)
        return PhaseStatus.RAN

    def _phase_proto(self, step: int) -> str:
        layer = self.components["protolanguage"]
        layer.process_context({"repeated_stimulus_patterns": {
            f"p{step % 3}": 3}})
        if self.bus:
            self.bus.publish(BusTopic.PROTO_SYMBOL, "protolanguage",
                             {"symbol_count":
                              layer.summary().get("symbol_count")}, step=step)
        return PhaseStatus.RAN

    def _phase_hypothesis(self, step: int) -> str:
        engine = self.components["hypothesis"]
        engine.tick(self._context())
        if self.bus:
            self.bus.publish(BusTopic.HYPOTHESIS, "hypothesis",
                             {"count": engine.summary().get(
                                 "hypothesis_count")}, step=step)
        return PhaseStatus.RAN

    def _phase_logos(self, step: int) -> str:
        engine = self.components["logos"]
        engine.tick(self._context())
        if self.bus:
            self.bus.publish(BusTopic.LOGOS_TENSION, "logos",
                             {"band": engine.summary().get(
                                 "complexity_band")}, step=step)
        return PhaseStatus.RAN

    def _phase_autoregen(self, step: int) -> str:
        engine = self.components["autoregeneration"]
        ctx = self._context()
        ctx["state_dir"] = self.context.state_dir
        engine.tick(ctx)
        if self.bus:
            self.bus.publish(BusTopic.DEGRADATION, "autoregeneration",
                             {"severity": engine.summary().get(
                                 "latest_degradation_severity")}, step=step)
        return PhaseStatus.RAN

    def _phase_inner_map(self, step: int) -> str:
        observer = self.components["inner_map"]
        observer.world_model = self.components.get("world_model")
        observer.active_perception = self.components.get("active_perception")
        observer.hypothesis = self.components.get("hypothesis")
        observer.autoregeneration = self.components.get("autoregeneration")
        observer.logos = self.components.get("logos")
        try:
            observer.update()
        except Exception:
            return PhaseStatus.DEGRADED
        if self.bus:
            self.bus.publish(BusTopic.INNER_MAP_UPDATE, "inner_map", {},
                             step=step)
        return PhaseStatus.RAN

    def _phase_telemetry(self, step: int) -> str:
        if self.bus:
            self.bus.publish(BusTopic.TELEMETRY, "orchestrator",
                             {"step": step, "counts": dict(self.counts)},
                             step=step)
        return PhaseStatus.RAN

    def _phase_latent(self, step: int) -> str:
        if self.bus:
            self.bus.publish(BusTopic.TELEMETRY, "latent_window",
                             {"window": "consolidation"}, step=step)
        return PhaseStatus.RAN

    # -- context for the higher engines -------------------------------------------

    def _context(self) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {"step": self.step_count,
                               "health_level": "ok"}
        wm = self.components.get("world_model")
        if wm is not None:
            try:
                ctx["world_model"] = wm.world_model_summary()
            except Exception:
                pass
        proto = self.components.get("protolanguage")
        if proto is not None:
            try:
                summary = proto.summary()
                ctx["proto_language"] = {
                    "symbol_count": summary.get("symbol_count", 0),
                    "ambiguous_symbol_count": summary.get(
                        "ambiguous_symbol_count", 0)}
            except Exception:
                pass
        nursery = self.components.get("ecology")
        if nursery is not None:
            try:
                ctx["ecology"] = nursery.summary()
                ctx["mysterium_pressure"] = 0.3
            except Exception:
                pass
        return ctx

    # -- control ------------------------------------------------------------------

    def _emergency_active(self) -> bool:
        if self.emergency_requested:
            return True
        try:
            from ..governance.emergency import EmergencyStop

            if self.context and self.context.state_dir:
                return EmergencyStop(
                    state_dir=self.context.state_dir).sentinel_present()
        except Exception:
            return False
        return False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def request_emergency_stop(self) -> None:
        self.emergency_requested = True

    def safe_shutdown(self, reason: str) -> None:
        if self.stopped:
            return
        self.stopped = True
        if self.lifecycle is not None:
            self.lifecycle.safe_shutdown_all(reason)
        if self.bus is not None:
            self.bus.publish(BusTopic.OPS_EVENT, "orchestrator",
                             {"event": "safe_shutdown", "reason": reason},
                             step=self.step_count)

    # -- views --------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        ctx = self.context
        return {
            "enabled": True,
            "run_id": ctx.run_id if ctx else None,
            "profile": (ctx.metadata.get("profile_id") if ctx else None),
            "mode": ctx.mode if ctx else None,
            "authority": ctx.authority if ctx else None,
            "current_spine_phase": self.spine.last_phase,
            "step_count": self.step_count,
            "enabled_modules": (self.registry.enabled()
                                if self.registry else []),
            "missing_modules": (self.registry.missing()
                                if self.registry else []),
            "degraded_modules": (self.lifecycle.degraded()
                                 if self.lifecycle else []),
            "bus_message_count": (self.bus.message_count()
                                  if self.bus else 0),
            "scheduler_skip_count": (self.scheduler.skip_count
                                     if self.scheduler else 0),
            "counts": dict(self.counts),
            "stopped": self.stopped,
            "refusal_reasons": list(self.refusal_reasons) or None,
            "full_system_report_path": getattr(self, "report_path", None),
            "authority_note": "no real-world action authority; "
                              "no module is sovereign",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "context": self.context.to_dict() if self.context else None,
            "summary": self.summary(),
            "spine": self.spine.snapshot(),
            "bus": self.bus.snapshot() if self.bus else None,
            "registry": self.registry.snapshot() if self.registry else None,
            "lifecycle": self.lifecycle.snapshot() if self.lifecycle else None,
            "scheduler": self.scheduler.snapshot() if self.scheduler else None,
            "safety": self.safety.snapshot(),
        }
