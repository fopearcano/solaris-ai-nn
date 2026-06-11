"""ContinuousRunner -- bounded (or explicitly continuous) long-running driver.

The runner ties the substrate to the continuity machinery. It owns:

* a :class:`SolarisNeuralBridge` (the low-compute neural substrate),
* a :class:`RuntimeLifecycle` (birth/heartbeat/death state machine),
* a :class:`PersistenceManager` (manifest / checkpoint / logs on disk).

On construction it restores prior state if the state directory already holds a
brain, detects whether the previous session died gracefully, and records the
*brain-death gap* (wall-clock time since the last heartbeat). It then runs a
loop that processes stimuli (external or, in silence, AION-style internal
continuity / absence stimuli), heartbeats, checkpoints periodically, and on exit
saves final state and a graceful-death record.

Boundedness is enforced: a run must be limited by ``max_steps``, ``max_duration_s``,
or an explicit ``continuous=True``. It never defaults to an unbounded loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from ..memory.trace_memory import TraceMemory
from ..plasticity.synthesis_pruning import SynthesisPruner
from ..signals import canonical as C
from ..signals.adapters import signal_to_dict
from ..signals.encoding import EventEncoder
from ..utils.logging import get_logger
from ..utils.math import norm
from . import persistence as P
from .lifecycle import RuntimeLifecycle
from .persistence import PersistenceManager, StateCheckpoint
from .telemetry import Telemetry

if TYPE_CHECKING:  # Imported lazily in __post_init__ to avoid an import cycle.
    from ..bridges.neural_bridge import SolarisNeuralBridge

logger = get_logger(__name__)

# Type aliases for the optional experiment-supplied callbacks.
StimulusProvider = Callable[[int], Optional[C.Stimulus]]
ReactionProvider = Callable[[Dict[str, Any], C.Stimulus], Optional[float]]


@dataclass
class ContinuousRunner:
    """Drive a neural bridge through a bounded long-running session.

    Args:
        state_dir: Directory for manifest/checkpoint/logs (one brain per dir).
        max_steps: Stop after this many session steps (None = unbounded on steps).
        max_duration_s: Stop after this much wall-clock time (None = no limit).
        heartbeat_interval_s: Minimum seconds between *logged* heartbeat events
            (the heartbeat timestamp itself updates every step).
        checkpoint_interval_steps: Checkpoint every N steps (0 disables).
        prune_interval_steps: Run a synthesis pass every N steps (0 disables).
        continuous: Explicitly allow an unbounded loop (must be set by the user).
        seed: Seed for a freshly-created brain (ignored if restoring; the saved
            seed is reused so the reservoir matrices match).
        action_labels / vocabulary: used to build the default bridge.
        bridge: An existing bridge to drive (otherwise one is created).
        stimulus_provider / reaction_provider: experiment callbacks.
        silence_threshold: Steps of external silence before absence stimuli begin.
    """

    state_dir: Union[str, Path] = ".solaris_ai_nn_state"
    max_steps: Optional[int] = None
    max_duration_s: Optional[float] = None
    heartbeat_interval_s: float = 1.0
    checkpoint_interval_steps: int = 50
    prune_interval_steps: int = 0
    continuous: bool = False
    seed: int = 0
    action_labels: List[str] = field(default_factory=lambda: ["approach", "withdraw", "consume"])
    vocabulary: Optional[List[str]] = None
    substrate_name: str = "esn"
    substrate_config: Optional[Dict[str, Any]] = None
    bridge: Optional[SolarisNeuralBridge] = None
    synthesis: SynthesisPruner = field(default_factory=SynthesisPruner)
    stimulus_provider: Optional[StimulusProvider] = None
    reaction_provider: Optional[ReactionProvider] = None
    silence_threshold: int = 5
    inner_map: bool = True
    inner_map_update_interval_steps: int = 10
    enable_plasticity: bool = False
    plasticity_interval_steps: int = 50
    plasticity_dry_run: bool = False
    enable_language: bool = False
    report_interval_steps: int = 100
    # Latent cognition (Prompt 14): bounded offline cycles during silence.
    # Disabled by default; dry-run (sandbox-only) by default when enabled.
    enable_latent: bool = False
    latent_interval_steps: int = 100
    latent_max_steps: int = 25
    latent_dry_run: bool = True
    allow_latent_plasticity: bool = False
    # World model (Prompt 15): persistent graph of observed structure.
    # Disabled by default; pruning is dry-run by default.
    enable_world_model: bool = False
    world_model_update_interval_steps: int = 25
    world_model_pruning_interval_steps: int = 250
    world_model_pruning_dry_run: bool = True
    # Homeostasis (Prompt 16): the need economy. Off by default; when on,
    # drive pressures bias bridge suggestions, never command anything.
    enable_homeostasis: bool = False
    homeostasis_update_interval_steps: int = 10
    homeostasis_report_interval_steps: int = 100
    # Executive (Prompt 17): arbitration between Desire and Action.
    # Off by default; the output is always a suggestion.
    enable_executive: bool = False
    executive_mode: str = "arbitrated"
    executive_report_interval_steps: int = 100

    def __post_init__(self) -> None:
        if not self.continuous and self.max_steps is None and self.max_duration_s is None:
            raise ValueError(
                "ContinuousRunner requires a bound: set max_steps and/or "
                "max_duration_s, or pass continuous=True explicitly."
            )
        self.pm = PersistenceManager(self.state_dir)
        self._stop_requested = False
        self._stop_reason = ""
        self._silence = 0
        self._absence_intensity = 0.0
        self._last_hb_log = 0.0
        self._last_checkpoint_ts = 0.0
        self.pruning_history: List[Dict[str, Any]] = []
        self._last_structural_summary: Optional[Dict[str, Any]] = None
        self._session_report = None
        self._init_session()
        self.observer = None
        if self.inner_map:
            from ..inner_map.observer import InnerMapObserver  # local: avoid cycle

            self.observer = InnerMapObserver(
                bridge=self.bridge, runner=self, synthesis=self.synthesis
            )

        # Optional controlled-plasticity engine (off by default).
        self.plasticity_engine = None
        if self.enable_plasticity:
            from ..plasticity.plasticity_engine import PlasticityEngine  # local: avoid cycle

            self.plasticity_engine = PlasticityEngine(
                bridge=self.bridge, synthesis=self.synthesis, runner=self,
                audit_path=str(self.pm.plasticity_audit_path),
                run_id=self.run_id, session_id=self.session_id,
                state_dir=str(self.pm.state_dir), dry_run=self.plasticity_dry_run,
            )
            # Restore mutable parameters saved by a previous session, if any.
            if self._restored_mutable_params:
                self.plasticity_engine.registry.apply_values(self._restored_mutable_params)
            # Rebuild rollback history from the audit so cross-session rollback works.
            self.plasticity_engine.load_history_from_audit()

        # Optional latent cognition (off by default; dry-run when on).
        self.latent = None
        if self.enable_latent:
            from ..latent.coordinator import LatentCognition  # local: avoid cycle

            self.latent = LatentCognition(
                bridge=self.bridge, state_dir=self.pm.state_dir,
                seed=self.seed, max_cycle_steps=self.latent_max_steps,
                dry_run=self.latent_dry_run,
                allow_plasticity=self.allow_latent_plasticity,
                plasticity_engine=self.plasticity_engine)

        # Optional homeostasis (off by default; bias only, never authority).
        self.homeostasis = None
        if self.enable_homeostasis:
            from ..homeostasis.regulation import HomeostaticRegulator

            self.homeostasis = HomeostaticRegulator(
                state_dir=self.pm.state_dir)
            self.bridge.enable_homeostasis = True
            self.bridge.homeostatic_regulator = self.homeostasis
            self._pending_valence_events: List[Dict[str, Any]] = []

        # Optional executive (off by default; suggestions only).
        self.executive = None
        if self.enable_executive:
            from ..executive.coordinator import ExecutiveLayer

            self.executive = ExecutiveLayer(state_dir=self.pm.state_dir,
                                            mode=self.executive_mode)
            self.bridge.enable_executive = True
            self.bridge.executive_layer = self.executive

        # Optional world model (off by default; restored from disk if saved).
        self.world_model = None
        if self.enable_world_model:
            from ..world_model.builder import WorldModelBuilder
            from ..world_model.serialization import load_graph

            self.world_model = WorldModelBuilder(
                anticipation=(self.latent.anticipation
                              if self.latent is not None else None),
                mysterium=(self.latent.mysterium
                           if self.latent is not None else None))
            saved = Path(self.pm.state_dir) / "world_model.json"
            if saved.exists():
                self.world_model.graph = load_graph(saved)
            if self.homeostasis is not None:
                # Need/drive/conflict structure flows into the graph.
                self.homeostasis.world_model = self.world_model

    # -- startup / restore --------------------------------------------------

    def _init_session(self) -> None:
        """Read prior manifest/checkpoint, build/restore the bridge, log startup."""
        manifest = self.pm.load_manifest()
        self.session_id = PersistenceManager.new_session_id()
        checkpoint = self.pm.load_checkpoint()

        if manifest is None:
            self.run_id = PersistenceManager.new_run_id()
            self.created_at = time.time()
            self.lifetime_base = 0
            self.restart_count = 0
            self.session_count = 1
            self.is_restart = False
            prev_graceful = True
            gap = 0.0
        else:
            self.run_id = manifest.get("run_id") or PersistenceManager.new_run_id()
            self.created_at = manifest.get("created_at", time.time())
            self.lifetime_base = int(manifest.get("lifetime_steps", 0))
            self.restart_count = int(manifest.get("restart_count", 0)) + 1
            self.session_count = int(manifest.get("session_count", 0)) + 1
            self.is_restart = True
            prev_graceful = bool(manifest.get("last_graceful_shutdown", True))
            last_hb = float(manifest.get("last_heartbeat_ts", 0.0) or 0.0)
            gap = max(0.0, time.time() - last_hb) if last_hb else 0.0

        # Build the bridge (reuse saved seed so substrate matrices are identical).
        seed = int(checkpoint.reservoir_config["seed"]) if checkpoint else self.seed
        if self.bridge is None:
            from ..bridges.neural_bridge import SolarisNeuralBridge  # local: avoid cycle

            encoder = EventEncoder(vocabulary=self.vocabulary)
            self.bridge = SolarisNeuralBridge(
                action_labels=self.action_labels, encoder=encoder, seed=seed,
                substrate_name=self.substrate_name,
                substrate_config=self.substrate_config,
                enable_language_trace=self.enable_language,
            )
        self.telemetry: Telemetry = self.bridge.telemetry

        # Continuity log + lifecycle, stamped with this session's identity.
        self.continuity = self.pm.continuity_log(self.run_id, self.session_id)
        self.lifecycle = RuntimeLifecycle(
            run_id=self.run_id,
            session_id=self.session_id,
            continuity_log=self.continuity,
            is_restart=self.is_restart,
        )

        # Restore substrate state (and pruning history) from the last checkpoint.
        self._restored_mutable_params: List[List[Any]] = []
        if checkpoint is not None:
            checkpoint.restore_into(self.bridge)
            self.pruning_history = list(checkpoint.pruning_history)
            self._restored_mutable_params = list(getattr(checkpoint, "mutable_params", []) or [])
        # Richer substrate state (membranes, refractory counters, ...) from the
        # generic npz store, when it matches the substrate we just built.
        self.pm.load_substrate_into(self.bridge.substrate)

        # Carry lifetime/restart counters into telemetry.
        self.telemetry.set_lifetime_steps(self.lifetime_base)
        self.telemetry.set_restarts(self.restart_count)

        # Replayable trace (append-only) under the state dir.
        self._trace = TraceMemory(path=self.pm.trace_path)

        # Record the prior death + the brain-death gap, before being reborn.
        if self.is_restart and not prev_graceful:
            self.continuity.log(
                P.UNEXPECTED_DEATH,
                "previous session did not record a graceful shutdown",
                lifetime_step=self.lifetime_base,
                graceful=False,
            )
            self.telemetry.record_unexpected_death(gap)
        if self.is_restart:
            self.continuity.log(
                P.BRAIN_DEATH_GAP,
                f"{gap:.3f}s elapsed since last heartbeat",
                lifetime_step=self.lifetime_base,
                graceful=prev_graceful,
                gap_seconds=gap,
            )
            self.telemetry.brain_death_gap_seconds = gap

        # Mark the manifest as "running / not gracefully shut down" immediately,
        # so a crash before the first checkpoint is still detectable next time.
        self._save_manifest(self.lifetime_base, graceful=False)

    # -- the loop -----------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Run the bounded (or explicitly continuous) session; return a snapshot."""
        self.lifecycle.birth(lifetime_step=self.lifetime_base)
        start = time.perf_counter()
        self._last_hb_log = start
        step = 0
        try:
            while not self._should_stop(step, start):
                step += 1
                lifetime = self.lifetime_base + step
                self._do_step(step, lifetime)
                if (
                    self.checkpoint_interval_steps > 0
                    and step % self.checkpoint_interval_steps == 0
                ):
                    self._checkpoint("interval", step, lifetime)
                if self.prune_interval_steps > 0 and step % self.prune_interval_steps == 0:
                    self._prune(step, lifetime)
                if (
                    self.observer is not None
                    and self.inner_map_update_interval_steps > 0
                    and step % self.inner_map_update_interval_steps == 0
                ):
                    self.observer.update()
                if (
                    self.plasticity_engine is not None
                    and self.plasticity_interval_steps > 0
                    and step % self.plasticity_interval_steps == 0
                ):
                    self.plasticity_engine.evaluate()
                if (
                    self.enable_language
                    and self.report_interval_steps > 0
                    and step % self.report_interval_steps == 0
                ):
                    self._last_structural_summary = self._structural_summary()
                if (
                    self.latent is not None
                    and self.latent_interval_steps > 0
                    and step % self.latent_interval_steps == 0
                ):
                    self._latent_tick(step, lifetime)
                if (
                    self.world_model is not None
                    and self.world_model_update_interval_steps > 0
                    and step % self.world_model_update_interval_steps == 0
                ):
                    self.world_model.update_from_trace(self.bridge.trace)
                if (
                    self.homeostasis is not None
                    and self.homeostasis_update_interval_steps > 0
                    and step % self.homeostasis_update_interval_steps == 0
                ):
                    self._homeostasis_tick(step)
                if (
                    self.homeostasis is not None
                    and self.homeostasis_report_interval_steps > 0
                    and step % self.homeostasis_report_interval_steps == 0
                ):
                    self._save_homeostasis(report=True)
                if (
                    self.executive is not None
                    and self.executive_report_interval_steps > 0
                    and step % self.executive_report_interval_steps == 0
                ):
                    self._executive_tick(step)
                if (
                    self.world_model is not None
                    and self.world_model_pruning_interval_steps > 0
                    and step % self.world_model_pruning_interval_steps == 0
                ):
                    # Synthesis over the graph: dry-run unless explicitly
                    # configured otherwise (governance gates production).
                    proposal = self.world_model.pruner.propose_pruning(
                        self.world_model.graph)
                    self.world_model.pruner.apply_pruning(
                        self.world_model.graph, proposal,
                        dry_run=self.world_model_pruning_dry_run)
        except KeyboardInterrupt:  # graceful: a Ctrl-C is still a clean death
            self._stop_requested = True
            self._stop_reason = "keyboard interrupt"
        self._finalize(step, graceful=True)
        return self.snapshot()

    def _do_step(self, step: int, lifetime: int) -> None:
        # bridge.process() advances telemetry.steps (one processed signal/step),
        # so session steps == telemetry.steps; no separate session counter needed.
        stim, is_external = self._next_stimulus(step)
        result = self.bridge.process(stim)
        if self.latent is not None:
            self.latent.note_step(result, is_external)
            if is_external:
                self.latent.reset_cooldowns()
        if self.world_model is not None:
            self.world_model.update_from_signal(stim, result, context={
                "latent": ({"mode": self.latent.controller.mode}
                           if self.latent is not None else None),
                "logos_fracture": result.get("logos_fracture"),
            })

        valence: Optional[float] = None
        if is_external and self.reaction_provider is not None:
            valence = self.reaction_provider(result, stim)
            if valence is not None:
                self.bridge.react(C.Reaction(valence=valence))
                self.telemetry.record_reinforcement()
                self._maybe_log_reinforcement(step, lifetime, valence)
                if self.world_model is not None:
                    self.world_model.update_from_reaction(
                        result["suggested_action"], valence)
                if self.homeostasis is not None:
                    self._pending_valence_events.append(
                        {"kind": "reaction", "value": valence})

        self._trace.record_signal(step, signal_to_dict(stim), lifetime, valence)

        self.lifecycle.heartbeat(step, lifetime)
        self.telemetry.heartbeat()
        self.telemetry.set_reservoir_norm(self.bridge.substrate_state_norm())
        self.telemetry.set_lifetime_steps(lifetime)

        now = time.perf_counter()
        if now - self._last_hb_log >= self.heartbeat_interval_s:
            self.continuity.log(P.HEARTBEAT, "alive", step=step, lifetime_step=lifetime)
            self._last_hb_log = now

    def _next_stimulus(self, step: int) -> "tuple[C.Stimulus, bool]":
        """Return the stimulus to process this step, and whether it is external.

        External stimuli come from the provider. In their absence the runner
        synthesises internal drive so the substrate never goes inert: a
        low-intensity continuity stimulus, escalating to an "I exist!" absence
        stimulus once silence passes ``silence_threshold`` (AION/Impulse).
        """
        if self.stimulus_provider is not None:
            external = self.stimulus_provider(step)
            if external is not None:
                self._silence = 0
                self._absence_intensity = 0.0
                return external, True
        self._silence += 1
        if self._silence >= self.silence_threshold:
            self._absence_intensity = min(1.0, self._absence_intensity + 0.1)
            return (
                C.Stimulus(
                    origin="aion",
                    modality="internal",
                    payload="I exist!",
                    intensity=self._absence_intensity,
                    is_absence=True,
                ),
                False,
            )
        return (
            C.Stimulus(origin="aion", modality="internal", payload=None, intensity=0.05),
            False,
        )

    # -- checkpoint / prune / finalize -------------------------------------

    def _checkpoint(self, reason: str, step: int, lifetime: int) -> None:
        self.lifecycle.checkpoint(reason, step=step, lifetime_step=lifetime)
        self.telemetry.checkpoint()
        mutable_params = None
        plasticity = None
        if self.plasticity_engine is not None:
            mutable_params = self.plasticity_engine.registry.snapshot_values()
            plasticity = self.plasticity_engine.snapshot()
        cp = StateCheckpoint.capture(
            self.bridge,
            run_id=self.run_id,
            session_id=self.session_id,
            session_step=step,
            lifetime_step=lifetime,
            last_heartbeat_ts=self.lifecycle.last_heartbeat_ts,
            pruning_history=self.pruning_history,
            mutable_params=mutable_params,
            plasticity=plasticity,
        )
        self.pm.save_checkpoint(cp)
        self.pm.save_substrate(self.bridge.substrate, step=lifetime)
        if self.enable_language:
            self._save_language_artifacts()
        self._last_checkpoint_ts = time.time()
        # Persist the Inner MAP self-model alongside the checkpoint.
        if self.observer is not None:
            self.pm.save_inner_map(self.observer.update().to_dict())
        if self.world_model is not None:
            self._save_world_model()
        if self.homeostasis is not None:
            self._save_homeostasis()
        if self.executive is not None:
            self.executive.save_state()
        self._save_manifest(lifetime, graceful=False)

    # -- homeostasis (optional) ------------------------------------------------

    def _homeostasis_tick(self, step: int) -> None:
        """One regulation update from the runner's live context."""
        events = self._pending_valence_events
        self._pending_valence_events = []
        context: Dict[str, Any] = {
            "step": step,
            "lifecycle": {
                "last_heartbeat_ts": self.lifecycle.last_heartbeat_ts,
                "last_checkpoint_ts": self._last_checkpoint_ts,
            },
            "telemetry": self.telemetry.to_dict(),
            "silence_duration": self._silence,
            "trace_length": len(self.bridge.trace),
            "trace_capacity": self.bridge.trace.capacity,
            "valence_events": events,
        }
        if self.latent is not None:
            context["latent"] = self.latent.summary()
        if self.world_model is not None:
            context["world_model"] = \
                self.world_model.world_model_summary()
        self.homeostasis.update(context)
        # Optional language trace: the dominant need as a grounded atom.
        if self.enable_language \
                and self.bridge.meaning_trace_builder is not None:
            summary = self.homeostasis.summary()
            if summary["dominant_need"]:
                from ..language.meaning_trace import atom

                self.bridge.meaning_trace_builder.append_atoms([atom(
                    "inner_map", "need pressure", "influenced",
                    f"dominant need {summary['dominant_need']} "
                    f"(intensity {summary['dominant_need_intensity']})",
                    source_module="homeostasis")])

    def _save_homeostasis(self, report: bool = False) -> None:
        if self.homeostasis is None:
            return
        self.homeostasis.save_state()
        if report:
            from ..homeostasis.reports import HomeostasisReportBuilder

            HomeostasisReportBuilder(self.homeostasis).save(
                Path(self.pm.state_dir) / "homeostasis_report.json",
                Path(self.pm.state_dir) / "homeostasis_report.md")

    # -- executive (optional) ----------------------------------------------------

    def _executive_tick(self, step: int) -> None:
        """One *recorded* arbitration with the runner's full context."""
        desires = []
        if self.homeostasis is not None \
                and self.homeostasis.last_result is not None:
            desires = list(self.homeostasis.last_result.desire_candidates)
        context: Dict[str, Any] = {
            "silence_duration": self._silence,
            "latent_mode": (self.latent.controller.mode
                            if self.latent is not None else "awake"),
            "mysterium_pressure": (self.latent.mysterium.pressure
                                   if self.latent is not None else 0.0),
            "habit_support": {
                action: weight for (pattern, action), weight
                in list(self.bridge.habit.weights.items())[:20]},
        }
        if self.world_model is not None:
            summary = self.world_model.world_model_summary()
            context["unknown_node_count"] = summary["unknown_node_count"]
        self.executive.decide(desires, context=context, step=step,
                              record=True)
        self.executive.save_state()

    def _save_world_model(self) -> None:
        from ..world_model.serialization import save_graph_exports

        save_graph_exports(self.world_model.graph, self.pm.state_dir)
        from ..world_model.reports import WorldModelReportBuilder

        WorldModelReportBuilder(builder=self.world_model).save(
            Path(self.pm.state_dir) / "world_model_report.json",
            Path(self.pm.state_dir) / "world_model_report.md")

    def _prune(self, step: int, lifetime: int) -> None:
        report = self.synthesis.prune(self.bridge.readout, self.bridge.habit)
        self.telemetry.pruning(report.total_removed)
        entry = {
            "step": step,
            "lifetime_step": lifetime,
            "removed": report.total_removed,
            "readout_zeroed": report.readout_zeroed,
            "habits_forgotten": report.habits_forgotten,
            "threshold": report.threshold,
        }
        self.pruning_history.append(entry)
        self.continuity.log(
            P.SYNTHESIS_PRUNING, report.summary(), step=step, lifetime_step=lifetime, **{
                "removed": report.total_removed,
            }
        )

    # -- latent cognition (optional) ------------------------------------------

    def _latent_tick(self, step: int, lifetime: int) -> None:
        """One scheduler evaluation; runs a bounded latent cycle if due.

        While a latent cycle runs, this loop is not processing external
        input -- external action execution is paused by construction.
        """
        summary = self.latent.maybe_cycle(
            step, silence=self._silence,
            run_id=self.run_id)
        if summary is not None:
            cycle_types = [c["type"] for c in summary["cycles"]]
            self.continuity.log(
                P.LATENT_CYCLE,
                f"latent cycle at step {step}: {', '.join(cycle_types) or 'none'}",
                step=step, lifetime_step=lifetime,
                cycles=cycle_types,
                mysterium=summary.get("mysterium_pressure"),
            )
            # Wake transition: the changes are summarized into the Inner MAP.
            if self.observer is not None:
                self.observer.update()
            self._save_latent_state()

    def _save_latent_state(self) -> None:
        if self.latent is None:
            return
        self.latent.save_report(
            Path(self.pm.state_dir) / "latent_report.json",
            Path(self.pm.state_dir) / "latent_report.md")

    def _maybe_log_reinforcement(self, step: int, lifetime: int, valence: float) -> None:
        # Throttle to one logged pair per checkpoint window to keep the log light.
        every = max(1, self.checkpoint_interval_steps)
        if self.telemetry.habit_reinforcements % every == 0:
            self.continuity.log(P.REACTION_FEEDBACK, "reaction applied", step=step,
                                lifetime_step=lifetime, valence=valence)
            self.continuity.log(P.HABIT_REINFORCEMENT, "habit reinforced", step=step,
                                lifetime_step=lifetime,
                                habit_pathways=len(self.bridge.habit.weights))

    def _finalize(self, step: int, graceful: bool) -> None:
        lifetime = self.lifetime_base + step
        # A final checkpoint captures the very latest state on the way out.
        self._checkpoint("final", step, lifetime)
        reason = self._stop_reason or "session complete"
        self.lifecycle.die(reason, graceful=graceful, step=step, lifetime_step=lifetime)
        self.telemetry.finish()
        self._save_manifest(lifetime, graceful=graceful, shutdown=True)
        self.pm.save_telemetry(self.telemetry.to_dict())
        if self.enable_language:
            self._save_session_report()
        if self.latent is not None:
            self._save_latent_state()
        if self.homeostasis is not None:
            self._save_homeostasis(report=True)
        self.continuity.close()

    # -- language layer (optional) ------------------------------------------

    def _language_context(self):
        """ExplanationContext grounded in this runner's full state."""
        extra: Dict[str, Any] = {}
        if self.observer is not None:
            extra["inner_map"] = self.observer.update().to_dict()
        if self.plasticity_engine is not None:
            extra["plasticity"] = self.plasticity_engine.snapshot()
        extra["pruning"] = {
            "passes": len(self.pruning_history),
            "removed": sum(int(p.get("removed", 0)) for p in self.pruning_history),
        }
        extra["continuity"] = {
            "restart_count": self.restart_count,
            "brain_death_gap_seconds": self.telemetry.brain_death_gap_seconds,
            "graceful_previous_shutdown": self.telemetry.unexpected_deaths == 0,
            "lifetime_steps": self.telemetry.lifetime_steps,
        }
        return self.bridge.explanation_context(**extra)

    def _structural_summary(self) -> Dict[str, Any]:
        from ..language.summarizer import StructuralSummarizer

        return StructuralSummarizer().summarize_session(self._language_context())

    def _save_language_artifacts(self) -> None:
        """Persist meaning trace (truncated), causal trace, and explanations."""
        from ..language import serialization as LS
        from ..language.causal_trace import CausalTraceBuilder

        builder = self.bridge.meaning_trace_builder
        if builder is not None:
            LS.save_meaning_trace(builder.to_trace(), self.pm.meaning_trace_path)
        causal = CausalTraceBuilder().build_from_recent_trace(self.bridge.trace)
        LS.save_causal_trace(causal, self.pm.causal_trace_path)
        engine = self.bridge.explanation_engine
        if engine is not None:
            ctx = self._language_context()
            from ..language.schemas import Explanation  # typing only

            explanations = {
                "last_event": engine.explain_last_event(ctx),
                "action_suggestion": engine.explain_action_suggestion(ctx),
                "substrate": engine.explain_substrate(ctx),
                "strongest_habit": engine.explain_strongest_habit(ctx),
                "continuity": engine.explain_continuity(ctx),
            }
            LS.save_explanations(explanations, self.pm.last_explanations_path)

    def _save_session_report(self) -> None:
        """Build + persist the session report (JSON + Markdown)."""
        from ..language import serialization as LS
        from ..language.reporting import ExperimentReportBuilder

        ctx = self._language_context()
        summary = self._structural_summary()
        builder = (
            ExperimentReportBuilder(title="Solaris-AI-NN session report")
            .add_metadata(run_id=self.run_id, session_id=self.session_id,
                          substrate=self.bridge.substrate.name,
                          state_dir=str(self.pm.state_dir))
            .add_section("runtime", {
                "steps": self.telemetry.steps,
                "lifetime_steps": self.telemetry.lifetime_steps,
                "duration_seconds": self.telemetry.to_dict()["duration_seconds"],
                "restarts": self.restart_count,
            })
            .add_section("signals", summary.get("signals"))
            .add_section("substrate", summary.get("substrate"))
            .add_section("habits", {
                "pathways": summary.get("habit_pathways"),
                "strongest": summary.get("strongest_habits"),
            })
            .add_section("synthesis", summary.get("pruning"))
            .add_section("plasticity", summary.get("plasticity"))
            .add_section("memory", {"trace_length": len(self.bridge.trace)})
            .add_section("inner_map", (ctx.inner_map or {}).get("continuity"))
            .add_section("continuity", summary.get("continuity"))
            .add_section("meaning_trace", summary.get("meaning_trace"))
        )
        self._session_report = builder.build()
        LS.save_report(self._session_report,
                       self.pm.session_report_json_path,
                       self.pm.session_report_md_path)

    def stop(self, reason: str = "stopped") -> None:
        """Request a graceful stop at the next loop boundary."""
        self._stop_requested = True
        self._stop_reason = reason

    def _should_stop(self, step: int, start: float) -> bool:
        if self._stop_requested:
            return True
        if self.max_steps is not None and step >= self.max_steps:
            return True
        if self.max_duration_s is not None and (time.perf_counter() - start) >= self.max_duration_s:
            return True
        return False

    # -- manifest / snapshot ------------------------------------------------

    def _save_manifest(self, lifetime_steps: int, graceful: bool, shutdown: bool = False) -> None:
        manifest = {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "session_count": self.session_count,
            "lifetime_steps": lifetime_steps,
            "restart_count": self.restart_count,
            "last_graceful_shutdown": graceful,
            "last_heartbeat_ts": self.lifecycle.last_heartbeat_ts or time.time(),
            "seed": int(self.bridge.substrate.seed),
        }
        if shutdown:
            manifest["last_shutdown_ts"] = time.time()
        self.pm.save_manifest(manifest)

    def snapshot(self) -> Dict[str, Any]:
        """Return a JSON-friendly view of the runner's current state.

        Includes telemetry, lifecycle, bridge, memory, inner_map, and boundaries.
        """
        snap: Dict[str, Any] = {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "state_dir": str(self.pm.state_dir),
            "continuity_log_path": str(self.pm.continuity_log_path),
            "inner_map_path": str(self.pm.inner_map_path),
            "lifecycle": self.lifecycle.snapshot(),
            "session_steps": self.telemetry.steps,
            "lifetime_steps": self.telemetry.lifetime_steps,
            "restart_count": self.restart_count,
            "checkpoints": self.telemetry.checkpoints,
            "unexpected_deaths": self.telemetry.unexpected_deaths,
            "brain_death_gap_seconds": self.telemetry.brain_death_gap_seconds,
            "reservoir_norm": self.bridge.substrate_state_norm(),
            "habit_pathways": len(self.bridge.habit.weights),
            "pruning_passes": len(self.pruning_history),
            "telemetry": self.telemetry.to_dict(),
            "bridge": self.bridge.snapshot(),
        }
        if self.observer is not None:
            model_dict = self.observer.update().to_dict()
            snap["inner_map"] = model_dict
            snap["memory"] = model_dict["memory"]
            snap["boundaries"] = self.observer.boundaries.to_dict()
        if self.plasticity_engine is not None:
            snap["plasticity"] = self.plasticity_engine.snapshot()
            snap["plasticity_audit_path"] = str(self.pm.plasticity_audit_path)
        if self.latent is not None:
            snap["latent"] = self.latent.summary()
        if self.world_model is not None:
            snap["world_model"] = self.world_model.world_model_summary()
        if self.homeostasis is not None:
            snap["homeostasis"] = self.homeostasis.summary()
        if self.executive is not None:
            snap["executive"] = self.executive.summary()
        if self.enable_language and self.bridge.meaning_trace_builder is not None:
            ctx = self._language_context()
            engine = self.bridge.explanation_engine
            snap["language"] = {
                "enabled": True,
                "meaning_atoms": len(self.bridge.meaning_trace_builder),
                "structural_summary": self._last_structural_summary,
                "last_event_explanation":
                    engine.explain_last_event(ctx).to_dict() if engine else None,
                "session_report_path": str(self.pm.session_report_md_path),
            }
        return snap

    # -- plasticity rollback ------------------------------------------------

    def rollback_last_plasticity(self):
        """Roll back the most recent applied plasticity step (if any)."""
        if self.plasticity_engine is None:
            raise RuntimeError("plasticity is not enabled on this runner")
        return self.plasticity_engine.rollback_last()

    def rollback_plasticity(self, step_id: str):
        """Roll back a specific plasticity step by id."""
        if self.plasticity_engine is None:
            raise RuntimeError("plasticity is not enabled on this runner")
        return self.plasticity_engine.rollback(step_id)
