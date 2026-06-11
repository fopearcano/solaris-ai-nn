"""SensorimotorSimulationRunner -- the bounded perceive/act/learn loop.

Per step:

1. the body **perceives** (sensors -> SensorReadings -> canonical Stimuli);
2. the **bridge** processes each stimulus (substrate update + suggestion);
3. the suggested action is **safety-validated** and, unless observe-only,
   **executed** by the body's effectors inside the GridWorld;
4. consequences become a **Reaction** (EmbodimentFeedback) and the bridge
   learns online; habit reinforces; plasticity (optional) tunes within bounds;
5. telemetry, Inner MAP, and persistence are updated.

Boundedness is mandatory: ``max_steps`` and/or ``max_duration_s``, or an
explicit ``continuous=True``. Action authority is simulation-only throughout.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..bridges.neural_bridge import SolarisNeuralBridge
from ..signals.encoding import EventEncoder
from ..utils.logging import get_logger
from .action_space import ALLOWED_ACTIONS
from .base import ActionResult, SensorReading
from .body import SimulatedBody
from .feedback import EmbodimentFeedback
from .grid_world import DANGER, REWARD, GridWorld
from .state import build_embodiment_state
from .sensors import SENSOR_VOCABULARY

logger = get_logger(__name__)


@dataclass
class SensorimotorSimulationRunner:
    """Drives body + world + bridge through a bounded sensorimotor session."""

    max_steps: Optional[int] = None
    max_duration_s: Optional[float] = None
    seed: int = 0
    state_dir: Optional[str] = None
    substrate: str = "esn"
    enable_plasticity: bool = False
    execute_suggestions: bool = True
    continuous: bool = False
    width: int = 9
    height: int = 7
    plasticity_interval_steps: int = 50
    inner_map_interval_steps: int = 25
    enable_language: bool = False
    # Latent cognition (Prompt 14): bounded dream/replay over body/world
    # traces during low-stimulus windows. Off by default; dry-run only here.
    enable_latent: bool = False
    latent_interval_steps: int = 50
    latent_max_steps: int = 20
    # World model (Prompt 15): observed GridWorld structure only -- no
    # pathfinding, no planning. Off by default.
    enable_world_model: bool = False
    world_model_update_interval_steps: int = 25
    world: Optional[GridWorld] = None
    body: Optional[SimulatedBody] = None
    bridge: Optional[SolarisNeuralBridge] = None
    feedback: EmbodimentFeedback = field(default_factory=EmbodimentFeedback)

    # Bounded histories + statistics.
    sensor_history: List[SensorReading] = field(default_factory=list, init=False)
    action_history: List[ActionResult] = field(default_factory=list, init=False)
    reaction_valences: List[float] = field(default_factory=list, init=False)
    action_counts: Counter = field(default_factory=Counter, init=False)
    collisions: int = field(default=0, init=False)
    rewards_consumed: int = field(default=0, init=False)
    reward_approaches: int = field(default=0, init=False)
    danger_escapes: int = field(default=0, init=False)
    steps_run: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.continuous and self.max_steps is None and self.max_duration_s is None:
            raise ValueError(
                "SensorimotorSimulationRunner requires a bound: set max_steps "
                "and/or max_duration_s, or pass continuous=True explicitly.")
        if self.world is None:
            self.world = GridWorld(width=self.width, height=self.height, seed=self.seed)
        if self.body is None:
            self.body = SimulatedBody(environment=self.world)
        if self.bridge is None:
            self.bridge = SolarisNeuralBridge(
                action_labels=list(ALLOWED_ACTIONS),
                encoder=EventEncoder(vocabulary=list(SENSOR_VOCABULARY)),
                substrate_name=self.substrate,
                seed=self.seed,
                enable_language_trace=self.enable_language,
            )
        self.last_explanations: Dict[str, Any] = {}
        self.observer = None
        self.plasticity_engine = None
        if self.enable_plasticity:
            from ..plasticity.plasticity_engine import PlasticityEngine
            from ..plasticity.synthesis_pruning import SynthesisPruner

            self.plasticity_engine = PlasticityEngine(
                bridge=self.bridge, synthesis=SynthesisPruner(),
                state_dir=self.state_dir or ".solaris_ai_nn_state/sensorimotor",
                run_id="embodied", session_id="embodied")
        self.latent = None
        self.latent_cycles = 0
        if self.enable_latent:
            from ..latent.coordinator import LatentCognition

            self.latent = LatentCognition(
                bridge=self.bridge,
                state_dir=self.state_dir
                or ".solaris_ai_nn_state/sensorimotor",
                seed=self.seed, max_cycle_steps=self.latent_max_steps,
                dry_run=True)  # embodied latent is always sandbox-only
        self.world_model = None
        if self.enable_world_model:
            from ..world_model.builder import WorldModelBuilder

            self.world_model = WorldModelBuilder(
                anticipation=(self.latent.anticipation
                              if self.latent is not None else None),
                mysterium=(self.latent.mysterium
                           if self.latent is not None else None))
        from ..inner_map.observer import InnerMapObserver

        self.observer = InnerMapObserver(bridge=self.bridge, embodiment=self,
                                         latent=self.latent,
                                         world_model=self.world_model)

    # -- the loop ---------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Run the bounded sensorimotor session; returns the final report."""
        start = time.perf_counter()
        step = 0
        while not self._should_stop(step, start):
            step += 1
            self._do_step(step)
            if (self.plasticity_engine is not None
                    and step % self.plasticity_interval_steps == 0):
                ctx = self.plasticity_engine.build_context()
                ctx.update(self.plasticity_context())
                self.plasticity_engine.apply_many(self.plasticity_engine.propose(ctx))
            if self.observer is not None and step % self.inner_map_interval_steps == 0:
                self.observer.update()
            if (self.latent is not None
                    and step % self.latent_interval_steps == 0):
                self._latent_tick(step)
            if (self.world_model is not None
                    and step % self.world_model_update_interval_steps == 0):
                self.world_model.update_from_embodiment(self)
        self.steps_run = step
        if self.world_model is not None:
            self.world_model.update_from_embodiment(self)
            if self.state_dir is not None:
                from ..world_model.serialization import save_graph_exports

                save_graph_exports(self.world_model.graph, self.state_dir)
        self.bridge.telemetry.finish()
        if self.state_dir is not None:
            self.persist()
        return self.report()

    def _latent_tick(self, step: int) -> None:
        """Bounded dream/replay over recent body/world traces.

        The cycle runs inline while the world is not being stepped, so no
        simulated action executes during dream/replay -- structurally. The
        recent reward/danger valences drive the silence proxy: a flat,
        low-stimulus window makes latent work due.
        """
        recent = self.reaction_valences[-20:]
        stimulus_quiet = not recent or max(abs(v) for v in recent) < 0.2
        actions_before = len(self.action_history)
        summary = self.latent.maybe_cycle(
            step,
            silence=self.latent.scheduler.sleep_after_silence
            if stimulus_quiet else 0,
            strategy="high_valence")
        assert len(self.action_history) == actions_before, \
            "latent cycle must not execute simulated actions"
        if summary is not None:
            self.latent_cycles += 1

    def _should_stop(self, step: int, start: float) -> bool:
        if self.max_steps is not None and step >= self.max_steps:
            return True
        if self.max_duration_s is not None and \
                (time.perf_counter() - start) >= self.max_duration_s:
            return True
        return False

    def _world_summary(self) -> Dict[str, Any]:
        nearest_reward = self.world.nearest(REWARD)
        nearest_danger = self.world.nearest(DANGER)
        return {
            "dist_reward": nearest_reward[2] if nearest_reward else None,
            "dist_danger": nearest_danger[2] if nearest_danger else None,
            "energy_low": self.body.energy.is_low,
            "energy_full": self.body.energy.energy >= self.body.energy.max_energy,
        }

    def _do_step(self, step: int) -> None:
        # 1. Perceive: every reading flows through the bridge as a signal.
        readings = self.body.perceive()
        self.sensor_history.extend(readings)
        self.sensor_history = self.sensor_history[-2000:]
        result_dict: Optional[Dict[str, Any]] = None
        for reading in readings:
            result_dict = self.bridge.process(reading.to_signal())
        if result_dict is None:
            return  # nothing sensed this step (possible with sparse sensors)

        if not self.execute_suggestions:
            return  # observe-only: perceive + learn substrate state, never act

        # 2. Act on the suggestion (safety-gated, simulation-only).
        action = result_dict["suggested_action"]
        before = self._world_summary()
        result = self.body.act(self.body.consider(action))
        self.action_history.append(result)
        self.action_history = self.action_history[-2000:]
        self.action_counts[action] += 1
        if result.blocked_reason in ("wall", "obstacle"):
            self.collisions += 1

        # 3. Feedback -> Reaction -> online learning.
        after = self._world_summary()
        reaction = self.feedback.evaluate(result, before, after)
        if reaction is not None:
            self.reaction_valences.append(reaction.valence)
            self.bridge.react(reaction)
            reasons = getattr(self.feedback, "last_reasons", [])
            if "closer_to_reward" in reasons or "consumed_reward" in reasons:
                self.reward_approaches += 1
            if "escaped_danger" in reasons:
                self.danger_escapes += 1
            if "consumed_reward" in reasons:
                self.rewards_consumed += 1

        # 4. Optional language layer: atoms + grounded per-step explanations.
        if self.enable_language and self.bridge.meaning_trace_builder is not None:
            self._explain_step(readings, result, reaction)

    def _explain_step(self, readings, result, reaction) -> None:
        """Record embodiment atoms and render the per-step explanations."""
        from ..language import templates as T

        builder = self.bridge.meaning_trace_builder
        builder.append_atoms(builder.from_embodiment_result(result.to_dict()))
        engine = self.bridge.explanation_engine
        ctx = self.bridge.explanation_context(
            embodiment=self.embodiment_summary(),
            last_result=result.to_dict(),
        )
        safety_report = self.body.safety.validate_action(result.action)
        self.last_explanations = {
            "sensor_reading": (
                f"Sensors emitted {len(readings)} reading(s): "
                + ", ".join(r.payload for r in readings) + "."
                if readings else "No sensor readings this step."),
            "suggested_action": engine.explain_action_suggestion(ctx).text,
            "safety_validation": (
                f"Safety validated {result.action!r}: "
                + ("safe simulated action" if safety_report.safe
                   else "; ".join(safety_report.violations)) + "."),
            "action_result": engine.explain_action_result(ctx).text,
            "reaction_feedback": (
                T.render("reaction_feedback", valence=round(reaction.valence, 3))
                if reaction is not None else
                "No feedback was generated for this step (neutral outcome)."),
        }

    # -- plasticity context (section 15) ------------------------------------------

    def plasticity_context(self) -> Dict[str, Any]:
        executed = self.body.actions_executed
        blocked = self.body.actions_blocked
        total = max(1, executed + blocked)
        return {
            "action_success_rate": executed / total,
            "action_failure_rate": blocked / total,
            "collision_count": self.collisions,
            "useless_action_count": self.feedback.useless_repeats,
            "reward_approach_success": self.reward_approaches,
            "danger_avoidance_success": self.danger_escapes,
            "energy_exhaustion_frequency": self.body.energy.exhaustion_events,
        }

    # -- inner map / persistence ----------------------------------------------------

    def embodiment_summary(self) -> Dict[str, Any]:
        """Compact embodiment status for the Inner MAP."""
        sense = self.world.sense()
        return {
            "body": True,
            "body_type": "SimulatedBody",
            "environment_type": "GridWorld",
            "position": list(self.body.position),
            "energy": self.body.energy.energy,
            "exhausted": self.body.energy.exhausted,
            "available_actions": list(ALLOWED_ACTIONS),
            "forbidden_actions": self.body.snapshot()["forbidden_actions"],
            "last_stimulus_types": [r.payload for r in self.body.last_readings],
            "last_action": self.body.last_result.action if self.body.last_result else None,
            "last_action_result": (self.body.last_result.consequence
                                   if self.body.last_result else None),
            "last_reaction_valence": (self.reaction_valences[-1]
                                      if self.reaction_valences else None),
            "environment_boundaries": {"width": self.world.width,
                                       "height": self.world.height},
            "nearby_objects": sense["nearby"],
            "action_authority": "simulation-only",
            "safety_status": self.body.safety.snapshot(),
        }

    def persist(self) -> Dict[str, str]:
        """Save embodiment/body/world state under ``state_dir``."""
        from ..runtime.persistence import PersistenceManager

        pm = PersistenceManager(self.state_dir)
        state = build_embodiment_state(self.body, self.world,
                                       self.sensor_history, self.action_history)
        pm.save_embodiment_state(state.to_dict())
        pm.save_body_state(self.body.snapshot())
        pm.save_world_state(self.world.snapshot())
        return {
            "embodiment_state": str(pm.embodiment_state_path),
            "body_state": str(pm.body_state_path),
            "world_state": str(pm.world_state_path),
        }

    # -- reporting --------------------------------------------------------------------

    def report(self) -> Dict[str, Any]:
        valences = self.reaction_valences
        return {
            "steps": self.steps_run,
            "observe_only": not self.execute_suggestions,
            "substrate": self.bridge.substrate.name,
            "action_counts": dict(self.action_counts),
            "actions_executed": self.body.actions_executed,
            "actions_blocked": self.body.actions_blocked,
            "collisions": self.collisions,
            "rewards_consumed": self.rewards_consumed,
            "reactions": {
                "count": len(valences),
                "positive": sum(1 for v in valences if v > 0),
                "negative": sum(1 for v in valences if v < 0),
                "mean_valence": (sum(valences) / len(valences)) if valences else 0.0,
            },
            "energy": self.body.energy.snapshot(),
            "substrate_metrics": self.bridge.substrate.metrics().to_dict(),
            "telemetry": self.bridge.telemetry.report(),
            "embodiment": self.embodiment_summary(),
            "plasticity": (self.plasticity_engine.snapshot()
                           if self.plasticity_engine else None),
            "language": ({
                "enabled": True,
                "meaning_atoms": len(self.bridge.meaning_trace_builder),
                "last_explanations": dict(self.last_explanations),
            } if self.enable_language
              and self.bridge.meaning_trace_builder is not None else None),
            "world_ascii": self.world.to_ascii(),
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.report()
