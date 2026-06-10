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

        valence: Optional[float] = None
        if is_external and self.reaction_provider is not None:
            valence = self.reaction_provider(result, stim)
            if valence is not None:
                self.bridge.react(C.Reaction(valence=valence))
                self.telemetry.record_reinforcement()
                self._maybe_log_reinforcement(step, lifetime, valence)

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
        self._last_checkpoint_ts = time.time()
        # Persist the Inner MAP self-model alongside the checkpoint.
        if self.observer is not None:
            self.pm.save_inner_map(self.observer.update().to_dict())
        self._save_manifest(lifetime, graceful=False)

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
        self.continuity.close()

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
