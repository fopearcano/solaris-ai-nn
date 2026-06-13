"""DevelopmentalRuntime -- a persistent developmental process, not a
training job.

The runtime wraps the bounded ContinuousRunner in *segments*: each
segment runs the full cognitive stack (homeostasis, executive, ego,
world model, latent cycles), then a maintenance tick advances the
developmental clock, ingests the segment into layered memory, applies the
consolidation policy, evaluates epochs, detects milestones and
phase-transition candidates, snapshots growth and drift, appends
autobiographical history, and saves the developmental state. Restarting
the runner between segments is deliberate: identity continuity across
restarts is one of the things being learned from.

Simulated time keeps tests at months-of-development in seconds-of-CPU;
real month/year-scale runs require explicit flags *and* governance
approval.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .autobiographical_memory import AutobiographicalMemory
from .consolidation_policy import ConsolidationPolicy
from .drift_monitor import LongRunDriftMonitor
from .epochs import EpochManager
from .growth_monitor import GrowthMonitor
from .long_horizon_metrics import long_horizon_metrics
from .memory_layers import MemoryLayerManager
from .milestones import MilestoneDetector
from .phase_transitions import PhaseTransitionDetector
from .safety import DevelopmentalSafetyValidator
from .timescales import DevelopmentalClock


@dataclass
class DevelopmentalRuntime:
    """Low-compute autonomous adaptation over very long runtime."""

    state_dir: Union[str, Path] = ".solaris_ai_nn_state/developmental"
    artifact_dir: Optional[Union[str, Path]] = None
    simulated_time: bool = True
    time_acceleration: float = 3600.0  # one step ~ one simulated hour
    target_runtime_days: Optional[int] = None
    enable_month_scale: bool = False
    enable_year_scale: bool = False
    max_steps: Optional[int] = 500
    max_duration_s: Optional[float] = None
    checkpoint_interval_steps: int = 50
    consolidation_interval_steps: int = 100
    epoch_check_interval_steps: int = 100
    long_report_interval_steps: int = 500
    seed: int = 7
    governance: Any = None
    stimulus_provider: Any = None
    reaction_provider: Any = None
    # Proto-language (Prompt 22): internal symbols from repetition.
    enable_proto_language: bool = False
    # Developmental nursery / stimulus ecology (Prompt 23).
    enable_ecology: bool = False
    nursery_config: Any = None
    ecology_report_interval_steps: int = 500
    ecology_event_log_path: Any = None
    # Active perception / intrinsic exploration (Prompt 24).
    enable_active_perception: bool = False
    active_perception_mode: str = "balanced"
    curiosity_driven_sampling: bool = False
    # Hypothesis engine / self-experimentation (Prompt 25).
    enable_hypothesis_engine: bool = False
    enable_hypothesis_world_model_updates: bool = False

    def __post_init__(self) -> None:
        self.state_dir = Path(self.state_dir)
        self.safety = DevelopmentalSafetyValidator()
        self.clock = self._load_clock()
        self.epochs = EpochManager()
        self.memory = MemoryLayerManager(state_dir=self.state_dir)
        self.policy = ConsolidationPolicy()
        self.growth = GrowthMonitor()
        self.drift = LongRunDriftMonitor()
        self.milestones = MilestoneDetector()
        self.phases = PhaseTransitionDetector()
        self.autobiography = AutobiographicalMemory(
            state_dir=self.state_dir)
        self.protolanguage = None
        if self.enable_proto_language:
            from ..protolanguage.layer import ProtoLanguageLayer

            self.protolanguage = ProtoLanguageLayer(
                state_dir=self.state_dir)
        self.nursery = None
        if self.enable_ecology:
            from ..ecology.nursery import (
                DevelopmentalNursery,
                NurseryConfig,
            )

            config = self.nursery_config or NurseryConfig(
                seed=self.seed,
                duration_steps=int(self.max_steps or 500),
                output_state_dir=self.state_dir)
            self.nursery = DevelopmentalNursery(
                config=config, governance=self.governance)
            # The ecology becomes the runtime's stimulus source.
            self.stimulus_provider = self.nursery.stimulus_provider
            self._ecology_base_step = 0
        self.active_perception = None
        if self.enable_active_perception:
            from ..active_perception.active_sensing import (
                ActiveSensingController,
            )
            from ..active_perception.exploration_memory import (
                ExplorationMemory,
            )
            from ..active_perception.sampling_policy import (
                SamplingPolicy,
                SamplingPolicyMode,
            )

            mode = (SamplingPolicyMode.CURIOSITY_DRIVEN
                    if self.curiosity_driven_sampling
                    else self.active_perception_mode)
            self.active_perception = ActiveSensingController(
                policy=SamplingPolicy(mode=mode, seed=self.seed),
                memory=ExplorationMemory(state_dir=self.state_dir),
                nursery=self.nursery, protolanguage=self.protolanguage,
                curiosity_enabled=self.curiosity_driven_sampling)
        self.hypothesis_engine = None
        if self.enable_hypothesis_engine:
            from ..hypothesis import HypothesisEngine

            self.hypothesis_engine = HypothesisEngine(
                state_dir=self.state_dir, nursery=self.nursery,
                protolanguage=self.protolanguage,
                active_perception=self.active_perception,
                governance=self.governance,
                enable_world_model_updates=(
                    self.enable_hypothesis_world_model_updates))
        self.segments_run = 0
        self.last_runner_snapshot: Dict[str, Any] = {}
        self.last_report_path: Optional[str] = None
        self._epoch_log_path = (self.state_dir
                                / "developmental_epochs.jsonl")
        self._state_path = self.state_dir / "developmental_state.json"

    def _load_clock(self) -> DevelopmentalClock:
        path = Path(self.state_dir) / "developmental_state.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                clock = DevelopmentalClock.from_dict(
                    data.get("clock", {}))
                clock.simulated = self.simulated_time
                clock.time_acceleration = self.time_acceleration
                return clock
            except (ValueError, OSError):
                pass
        return DevelopmentalClock(simulated=self.simulated_time,
                                  time_acceleration=self.time_acceleration)

    # -- the long loop ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Run all segments with maintenance between them."""
        config_report = self.safety.validate_config(self,
                                                    self.governance)
        if not config_report.safe:
            raise PermissionError("developmental run refused: "
                                  + "; ".join(config_report.violations))
        paths_report = self.safety.validate_paths(self.state_dir,
                                                  self.artifact_dir)
        if not paths_report.safe:
            raise PermissionError("; ".join(paths_report.violations))
        total = int(self.max_steps or 500)
        segment_size = max(1, min(self.consolidation_interval_steps,
                                  total))
        steps_done = 0
        if self.segments_run == 0 and not self.autobiography.events:
            self.autobiography.add(
                "Developmental run started.",
                evidence=[f"state_dir:{self.state_dir}",
                          f"simulated:{self.simulated_time}"],
                category="runtime", simulated=self.simulated_time)
        while steps_done < total:
            steps = min(segment_size, total - steps_done)
            snapshot = self._run_segment(steps)
            steps_done += steps
            self._maintenance_tick(snapshot, steps)
        self.save_state()
        return self.snapshot()

    def _run_segment(self, steps: int) -> Dict[str, Any]:
        from ..runtime.continuous_runner import ContinuousRunner
        from ..signals import canonical as C

        provider = self.stimulus_provider or (
            lambda step: C.Stimulus(payload=f"p{step % 3}",
                                    intensity=0.5)
            if step % 4 != 0 else None)
        runner = ContinuousRunner(
            state_dir=str(self.state_dir / "runner"),
            max_steps=steps, seed=self.seed,
            checkpoint_interval_steps=self.checkpoint_interval_steps,
            stimulus_provider=provider,
            reaction_provider=self.reaction_provider
            or (lambda result, stim: 1.0
                if result.get("suggested_action") == "approach"
                else 0.0),
            enable_homeostasis=True,
            homeostasis_update_interval_steps=25,
            enable_executive=True, executive_report_interval_steps=50,
            enable_ego=True, ego_update_interval_steps=50,
            enable_world_model=True,
            enable_latent=True, latent_interval_steps=40)
        runner.developmental = self  # supervisors may observe through us
        snapshot = runner.run()
        self.segments_run += 1
        self.last_runner_snapshot = snapshot
        if self.simulated_time:
            self.clock.advance(steps)  # 1 step == 1s, accelerated
        else:
            self.clock.tick_real()
        gap = float(snapshot.get("brain_death_gap_seconds", 0.0) or 0.0)
        if gap > 5.0:
            self.clock.note_restart_gap(gap, "segment restart gap")
        self.clock.total_observed_stimuli += int(
            snapshot.get("session_steps", steps) or steps)
        latent = snapshot.get("latent") or {}
        self.clock.total_latent_cycles += int(
            latent.get("cycles_completed", latent.get("cycles", 0)) or 0)
        world = snapshot.get("world_model") or {}
        self.clock.total_world_model_updates += int(
            world.get("graph_node_count", 0) or 0)
        self.clock.note_checkpoint()
        return snapshot

    # -- maintenance ----------------------------------------------------------------

    def _maintenance_tick(self, snapshot: Dict[str, Any],
                          steps: int) -> None:
        lifetime = self.clock.cumulative_lifetime_s
        signals = self._signals(snapshot)
        # 1. Ingest segment evidence into hot memory.
        for kind, content in self._segment_events(snapshot):
            self.memory.add_hot(content, kind=kind,
                                lifetime_s=lifetime)
        # 2. Consolidation policy over the hot layer.
        report = self.policy.apply(self.memory, lifetime_s=lifetime)
        self.clock.note_consolidation()
        self.safety.validate_memory(self.memory)
        # 3. Growth, drift, phases, epochs, milestones.
        growth_snapshot = self.growth.observe(signals,
                                              lifetime_s=lifetime)
        self.drift.observe(self._drift_values(snapshot),
                           lifetime_s=lifetime)
        new_candidates = self.phases.observe(signals,
                                             lifetime_s=lifetime)
        signals["phase_transition_candidates"] = len(
            self.phases.candidates)
        signals["stagnation_windows"] = self.growth.stagnation_windows
        signals["consolidation_count"] = \
            self.clock.total_memory_consolidations
        if self.protolanguage is not None:
            self._proto_language_tick(snapshot, signals, lifetime)
        if self.nursery is not None:
            self._ecology_tick(signals, lifetime)
        if self.active_perception is not None:
            self._active_perception_tick(snapshot, signals, lifetime)
        if self.hypothesis_engine is not None:
            self._hypothesis_tick(snapshot, signals, lifetime)
        transition = self.epochs.evaluate(signals, lifetime_s=lifetime)
        if transition is not None:
            self.clock.note_epoch_transition()
            self._log_epoch(transition)
            self.autobiography.add(
                f"Developmental epoch label changed from "
                f"{transition.from_epoch} to {transition.to_epoch} "
                f"({transition.reason}).",
                evidence=[f"signals:{sorted(transition.signals)[:3]}"],
                category="epoch", lifetime_s=lifetime,
                simulated=self.simulated_time)
        for milestone in self.milestones.detect(
                signals, lifetime_s=lifetime,
                simulated=self.simulated_time):
            self.memory.record_fossil(milestone.to_dict(),
                                      kind=milestone.type,
                                      lifetime_s=lifetime)
            self.autobiography.record_milestone(milestone)
        for candidate in new_candidates:
            self.autobiography.add(
                f"Phase-transition candidate recorded: {candidate.kind} "
                f"({candidate.metric} {candidate.before} -> "
                f"{candidate.after}). This is a hypothesis, not proof "
                "of emergence.",
                evidence=[f"metric:{candidate.metric}",
                          f"delta:{candidate.delta}"],
                category="phase", lifetime_s=lifetime,
                simulated=self.simulated_time)
        del report, growth_snapshot  # recorded in their own monitors
        self.save_state()

    def _proto_language_tick(self, snapshot: Dict[str, Any],
                             signals: Dict[str, Any],
                             lifetime: float) -> None:
        """Scan the segment for symbol emergence; fossilize the firsts."""
        layer = self.protolanguage
        habit_count = int(snapshot.get("habit_pathways", 0) or 0)
        latent = snapshot.get("latent") or {}
        ego = snapshot.get("ego") or {}
        executive = snapshot.get("executive") or {}
        proto_context = {
            "label": f"segment_{self.segments_run}",
            "repeated_stimulus_patterns": {
                "session_stimuli": signals.get(
                    "total_observed_stimuli", 0)},
            "absence_states": {"silence_windows": 3}
            if snapshot.get("session_steps") else {},
            "action_reaction_loops": {
                f"habit_pathways_{habit_count}": habit_count},
            "mysterium_spikes": (
                {"mysterium_high": 3}
                if float(latent.get("mysterium_pressure", 0.0)
                         or 0.0) > 0.6 else {}),
            "boundary_events": (
                {"boundary_violation":
                 int(ego.get("boundary_violation_count", 0) or 0)}
                if ego.get("boundary_violation_count") else {}),
            "executive_inhibitions": (
                {"inhibition": int(executive.get(
                    "inhibited_candidate_count", 0) or 0)}
                if executive.get("inhibited_candidate_count") else {}),
            "need_pressures": {"regulation_updates": 3},
            "world_model_entities": {
                "graph_growth": signals.get("world_model_node_count",
                                            0)},
            "milestones": [m.type for m in
                           self.milestones.registry.milestones[-3:]],
        }
        if self.nursery is not None:
            # Ground proto-symbols in the actual ecology the system met.
            eco = self.nursery.summary()
            proto_context["absence_states"] = {
                "nursery_absence": int(eco["absence_window_count"])}
            if eco["anomaly_count"]:
                proto_context["mysterium_spikes"] = {
                    "nursery_anomaly": int(eco["anomaly_count"])}
            if eco["delayed_consequence_group_count"]:
                proto_context["world_model_contexts"] = {
                    "delayed_consequence":
                        int(eco["delayed_consequence_group_count"])}
            proto_context["context_symbols"] = {
                f"season_{eco['current_season']}": 3}
            proto_context["world_model_entities"] = {
                f"regime_{eco['current_regime']}": 3}
        scan = layer.process_context(proto_context, lifetime_s=lifetime)
        born = int(scan.get("born", 0) or 0)
        if born:
            for symbol in sorted(layer.registry.symbols.values(),
                                 key=lambda s: -s.created_at)[:born]:
                self.memory.record_fossil(
                    {"description": f"proto-symbol born: "
                                    f"{symbol.token}",
                     "kind": "proto_symbol_birth",
                     "token": symbol.token},
                    kind="proto_symbol_birth", lifetime_s=lifetime)
        layer.save_state()
        summary = layer.summary()
        signals["proto_symbol_count"] = summary["symbol_count"]
        signals["stable_symbol_count"] = max(
            signals.get("stable_symbol_count", 0),
            summary["stable_symbol_count"])
        signals["symbol_sequence_count"] = summary["sequence_count"]
        signals["proto_syntax_rule_count"] = summary[
            "proto_syntax_rule_count"]
        signals["symbol_prediction_improvement"] = summary[
            "prediction_utility"]
        signals["proto_utterance_count"] = (
            layer.utterances.built)
        signals["symbol_extinction_count"] = sum(
            1 for s in layer.registry.symbols.values()
            if s.status == "extinct")

    def _ecology_tick(self, signals: Dict[str, Any],
                      lifetime: float) -> None:
        """Inject nursery-derived signals so ecology milestones can fire."""
        eco = self.nursery.summary()
        signals["nursery_absence_windows"] = int(
            eco["absence_window_count"])
        signals["nursery_seasonal_shifts"] = int(
            eco["seasonal_shift_count"])
        signals["nursery_delayed_groups"] = int(
            eco["delayed_consequence_group_count"])
        signals["nursery_anomaly_events"] = int(eco["anomaly_count"])
        signals["nursery_boundary_events"] = int(
            self.nursery.memory.event_counts.get("boundary_event", 0))
        signals["nursery_deprivation_recoveries"] = int(
            self.nursery.ecology.deprivation.deprived_steps > 0
            and not self.nursery.ecology.deprivation.active)
        signals["nursery_ecology_utterances"] = int(
            self.protolanguage.utterances.built
            if self.protolanguage is not None else 0)
        # Close one ecology episode per segment with the developmental
        # response that co-occurred (correlation, not proof).
        self.nursery.close_episode(self.segments_run, {
            "growth_status": (self.growth.latest().classification
                              if self.growth.latest() else None),
            "structural_change_score": signals.get(
                "structural_change_score", 0.0)})

    def _active_perception_tick(self, snapshot: Dict[str, Any],
                                signals: Dict[str, Any],
                                lifetime: float) -> None:
        """Run one self-directed sampling decision over the segment context."""
        controller = self.active_perception
        latent = snapshot.get("latent") or {}
        # Build a normalized context from this segment's measured signals.
        before = controller.build_context({
            "step": self.segments_run,
            "mysterium_pressure": float(latent.get("mysterium_pressure", 0.0)
                                        or 0.0),
            "prediction_error": float(
                signals.get("recent_prediction_error", 0.0) or 0.0),
            "structural_change_score": float(
                signals.get("structural_change_score", 0.0) or 0.0),
            "stagnation_status": ("stagnating"
                                  if signals.get("stagnation_windows", 0)
                                  else None),
            "health_level": "ok",
        })
        decision = controller.select(before)
        result = controller.execute_if_allowed(decision, before)
        after = controller.build_context({"step": self.segments_run + 1})
        controller.observe_result(result, before, after)
        # Surface sampling signals for milestones/ops/inner map.
        snap = controller.snapshot()
        memory = snap.get("exploration_memory") or {}
        signals["sampling_action_count"] = int(
            memory.get("record_count", 0) or 0)
        signals["useful_sampling_rate"] = float(
            memory.get("useful_rate", 0.0) or 0.0)
        signals["blocked_sampling_count"] = int(
            snap.get("blocked_count", 0) or 0)
        signals["curiosity_pressure"] = float(
            (snap.get("curiosity") or {}).get("pressure", 0.0) or 0.0)

    def _hypothesis_tick(self, snapshot: Dict[str, Any],
                         signals: Dict[str, Any], lifetime: float) -> None:
        """Run one scan -> generate -> bounded-test hypothesis cycle."""
        engine = self.hypothesis_engine
        latent = snapshot.get("latent") or {}
        world = snapshot.get("world_model") or {}
        proto = (self.protolanguage.summary()
                 if self.protolanguage is not None else {})
        ctx = {
            "step": self.segments_run,
            "mysterium_pressure": float(latent.get("mysterium_pressure", 0.0)
                                        or 0.0),
            "prediction_error": float(
                signals.get("recent_prediction_error", 0.0) or 0.0),
            "structural_change_score": float(
                signals.get("structural_change_score", 0.0) or 0.0),
            "stagnation_status": ("stagnating"
                                  if signals.get("stagnation_windows", 0)
                                  else None),
            "world_model": world,
            "proto_language": {
                "symbol_count": proto.get("symbol_count", 0),
                "ambiguous_symbol_count": proto.get(
                    "ambiguous_symbol_count", 0)},
            "ecology": (self.nursery.summary()
                        if self.nursery is not None else {}),
            "health_level": "ok",
        }
        engine.tick(ctx)
        summary = engine.summary()
        signals["hypothesis_count"] = int(summary.get("hypothesis_count", 0))
        signals["hypothesis_supported_count"] = int(
            summary.get("supported_count", 0))
        signals["hypothesis_falsified_count"] = int(
            summary.get("falsified_count", 0))
        signals["hypothesis_tests_run"] = int(summary.get("tests_run", 0))

    def _signals(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        habit_weights = ((snapshot.get("bridge") or {}).get("habit")
                         or {})
        stable_habits = (habit_weights.get("strong_pathways")
                         if isinstance(habit_weights, dict) else None)
        if stable_habits is None:
            stable_habits = int(snapshot.get("habit_pathways", 0) or 0)
        world = snapshot.get("world_model") or {}
        latent = snapshot.get("latent") or {}
        ego = snapshot.get("ego") or {}
        executive = snapshot.get("executive") or {}
        telemetry = snapshot.get("telemetry") or {}
        accuracy = float(telemetry.get("rolling_accuracy",
                                       telemetry.get("accuracy", 0.0))
                         or 0.0)
        return {
            "runtime_hours": self.clock.age_in("session"),
            "total_observed_stimuli":
                self.clock.total_observed_stimuli,
            "stable_habit_count": int(stable_habits or 0),
            "habit_turnover": 0,
            "world_model_node_count": int(
                world.get("graph_node_count", 0) or 0),
            "world_model_edge_count": int(
                world.get("graph_edge_count", 0) or 0),
            "unknown_node_count": int(
                world.get("unknown_node_count", 0) or 0),
            "consolidated_schema_count": int(
                latent.get("consolidated_schema_count", 0) or 0),
            "latent_replay_count": int(
                latent.get("replay_count", latent.get("cycles", 0))
                or 0),
            "prediction_accuracy": accuracy,
            "prediction_accuracy_trend": 0.0,
            "mysterium_pressure": float(
                latent.get("mysterium_pressure", 0.0) or 0.0),
            "mysterium_trend": 0.0,
            "pruning_count": int(snapshot.get("pruning_passes", 0)
                                 or 0),
            "restart_stability": 1.0 if not snapshot.get(
                "unexpected_deaths") else 0.5,
            "restart_recovery_count": int(
                snapshot.get("restart_count", 0) or 0),
            "pruning_stability": 1.0,
            "no_safe_action_rate": float(
                executive.get("no_safe_action_count", 0) or 0)
            / max(1, int(executive.get("decisions", 1) or 1)),
            "homeostatic_stability": 1.0,
            "boundary_violation_count": int(
                ego.get("boundary_violation_count", 0) or 0),
            "identity_continuity": float(
                ego.get("identity_continuity", 1.0) or 1.0),
            "executive_decision_diversity": 0.0,
            "meaning_atom_count": int(
                (snapshot.get("language") or {}).get(
                    "meaning_atom_count", 0) or 0),
        }

    def _drift_values(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        ego = snapshot.get("ego") or {}
        latent = snapshot.get("latent") or {}
        world = snapshot.get("world_model") or {}
        return {
            "substrate_state_norm": float(
                snapshot.get("reservoir_norm", 0.0) or 0.0),
            "habit_weight_total": float(
                snapshot.get("habit_pathways", 0) or 0),
            "world_model_node_count": float(
                world.get("graph_node_count", 0) or 0),
            "mysterium_pressure": float(
                latent.get("mysterium_pressure", 0.0) or 0.0),
            "identity_continuity": float(
                ego.get("identity_continuity", 1.0) or 1.0),
            "boundary_violation_count": float(
                ego.get("boundary_violation_count", 0) or 0),
        }

    @staticmethod
    def _segment_events(snapshot: Dict[str, Any],
                        ) -> List["tuple[str, Dict[str, Any]]"]:
        events: List = [("segment_summary", {
            "steps": snapshot.get("session_steps"),
            "lifetime_steps": snapshot.get("lifetime_steps"),
            "habit_pathways": snapshot.get("habit_pathways")})]
        ego = snapshot.get("ego") or {}
        if ego.get("identity_warnings"):
            events.append(("identity_warning",
                           {"warnings": ego["identity_warnings"][:2]}))
        if ego.get("boundary_violation_count"):
            events.append(("boundary_violation", {
                "count": ego["boundary_violation_count"]}))
        latent = snapshot.get("latent") or {}
        if float(latent.get("mysterium_pressure", 0.0) or 0.0) > 0.6:
            events.append(("mysterium_spike", {
                "pressure": latent["mysterium_pressure"]}))
        world = snapshot.get("world_model") or {}
        if world:
            events.append(("world_model_growth", {
                "nodes": world.get("graph_node_count"),
                "edges": world.get("graph_edge_count")}))
        return events

    def _log_epoch(self, transition: Any) -> None:
        self._epoch_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._epoch_log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(transition.to_dict(), default=str)
                     + "\n")

    # -- persistence / views --------------------------------------------------------------

    def save_state(self) -> str:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(self.snapshot(), fh, indent=2, default=str)
        return str(self._state_path)

    def developmental_pressures(self) -> Dict[str, Any]:
        """Pressure dict for homeostasis (never commands)."""
        return {
            "stagnation_pressure": min(
                1.0, 0.2 * self.growth.stagnation_windows),
            "drift_pressure": min(1.0, self.drift.mean_drift_velocity()),
            "memory_pressure": (1.0 if self.memory.over_budget_layers()
                                else 0.0),
            "consolidation_need": min(
                1.0, self.clock.checkpoint_age_s() / 3600.0),
            "identity_continuity": self._signal_identity(),
            "long_run_fatigue_proxy": min(
                1.0, self.clock.age_in("daily") / 30.0),
        }

    def _signal_identity(self) -> float:
        ego = (self.last_runner_snapshot.get("ego") or {})
        return float(ego.get("identity_continuity", 1.0) or 1.0)

    def summary(self) -> Dict[str, Any]:
        """Compact status for ops / Inner MAP."""
        latest_growth = self.growth.latest()
        latest_drift = self.drift.latest()
        latest_milestone = (self.milestones.registry.milestones[-1]
                            if self.milestones.registry.milestones
                            else None)
        return {
            "enabled": True,
            "simulated_time": self.simulated_time,
            "current_epoch": self.epochs.state.current,
            "developmental_age_hours": round(
                self.clock.age_in("session"), 4),
            "clock": self.clock.to_dict(),
            "memory_layers": self.memory.state().to_dict(),
            "last_consolidation_at_s":
                self.clock.last_consolidation_at_s,
            "last_milestone": (latest_milestone.to_dict()
                               if latest_milestone else None),
            "milestone_count": len(self.milestones.registry.milestones),
            "fossil_memory_count": self.memory.state().fossil_count,
            "growth_status": (latest_growth.classification
                              if latest_growth else None),
            "structural_change_score": (
                latest_growth.structural_change_score
                if latest_growth else 0.0),
            "drift_status": (latest_drift.classification
                             if latest_drift else None),
            "phase_transition_candidates": len(self.phases.candidates),
            "stagnation_windows": self.growth.stagnation_windows,
            "segments_run": self.segments_run,
            "next_long_report_after_steps":
                self.long_report_interval_steps,
            "developmental_report_path": self.last_report_path,
            "proto_language": (self.protolanguage.summary()
                               if self.protolanguage is not None
                               else None),
            "ecology": (self.nursery.summary()
                        if self.nursery is not None else None),
            "active_perception": (self.active_perception.snapshot()
                                  if self.active_perception is not None
                                  else None),
            "hypothesis": (self.hypothesis_engine.summary()
                           if self.hypothesis_engine is not None else None),
            "note": "a persistent developmental process; labels are "
                    "measurements, not consciousness claims",
        }

    def long_horizon_state(self) -> Dict[str, Any]:
        signals = self._signals(self.last_runner_snapshot or {})
        return {
            "clock": self.clock.to_dict(),
            "memory": self.memory.state().to_dict(),
            "growth": self.growth.snapshot(),
            "drift": self.drift.snapshot(),
            "milestones": self.milestones.snapshot(),
            "epochs": self.epochs.snapshot(),
            "identity_continuity": signals.get("identity_continuity",
                                               1.0),
            "boundary_violation_count": signals.get(
                "boundary_violation_count", 0),
            "world_model_node_count": signals.get(
                "world_model_node_count", 0),
            "pruning_count": signals.get("pruning_count", 0),
            "prediction_accuracy_trend": signals.get(
                "prediction_accuracy_trend", 0.0),
            "phase_transition_candidates": len(self.phases.candidates),
        }

    def metrics(self) -> Dict[str, Any]:
        return long_horizon_metrics(self.long_horizon_state())

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "clock": self.clock.to_dict(),
            "epochs": self.epochs.snapshot(),
            "memory": self.memory.snapshot(),
            "consolidation": self.policy.snapshot(),
            "growth": self.growth.snapshot(),
            "drift": self.drift.snapshot(),
            "milestones": self.milestones.snapshot(),
            "phases": self.phases.snapshot(),
            "autobiography": self.autobiography.snapshot(),
            "safety": self.safety.snapshot(),
            "ecology": (self.nursery.snapshot()
                        if self.nursery is not None else None),
            "active_perception": (self.active_perception.snapshot()
                                  if self.active_perception is not None
                                  else None),
            "hypothesis": (self.hypothesis_engine.snapshot()
                           if self.hypothesis_engine is not None else None),
            "metrics": self.metrics(),
        }
