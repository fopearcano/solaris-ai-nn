"""LatentCognition -- the one object a runner wires in to go latent.

Bundles the controller, scheduler, trackers, cycles, store, and safety into
a single per-step API: ``note_step`` feeds anticipation/Mysterium during
awake processing, and ``maybe_cycle`` runs at the configured interval --
asking the scheduler, executing one bounded latent sequence
(sleep -> consolidation and/or replay/dream -> wake) and returning the wake
summary. While a cycle runs, the runner is by construction not processing
external input, so no external action can occur.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .anticipation import AnticipationTracker
from .complexity_pressure import ComplexityPressureMonitor
from .dream_cycle import DreamCycle
from .latent_memory import LatentMemoryStore
from .latent_report import LatentReportBuilder
from .modes import LatentMode, SleepWakeController
from .mysterium import MysteriumTracker
from .offline_replay import OfflineReplayEngine
from .safety import LatentSafetyValidator
from .scheduler import LatentDecision, LatentScheduler
from .sleep_cycle import SleepCycle


@dataclass
class LatentCognition:
    """Everything a runner needs for bounded latent processing."""

    bridge: Any  # SolarisNeuralBridge
    state_dir: Union[str, Path] = ".solaris_ai_nn_state"
    seed: int = 0
    max_cycle_steps: int = 25
    dry_run: bool = True
    allow_plasticity: bool = False
    governance: Any = None
    plasticity_engine: Any = None

    cycle_log: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.controller = SleepWakeController()
        self.safety = LatentSafetyValidator()
        self.scheduler = LatentScheduler(controller=self.controller,
                                         safety=self.safety)
        self.store = LatentMemoryStore(self.state_dir)
        self.anticipation = AnticipationTracker()
        self.mysterium = MysteriumTracker()
        self.complexity = ComplexityPressureMonitor()
        self.replay_engine = OfflineReplayEngine(seed=self.seed)
        self.sleep_cycle = SleepCycle(bridge=self.bridge, store=self.store,
                                      safety=self.safety)
        self.dream_cycle = DreamCycle(
            bridge=self.bridge, store=self.store,
            replay_engine=self.replay_engine,
            anticipation=self.anticipation, mysterium=self.mysterium,
            safety=self.safety, governance=self.governance,
            allow_production_mutation=self.allow_plasticity
            and not self.dry_run,
            seed=self.seed)
        self._last_report_paths: Optional[Dict[str, Any]] = None
        self._consolidated_recently = False
        self._replayed_recently = False

    # -- per-step (awake) ---------------------------------------------------------

    def note_step(self, result: Dict[str, Any],
                  is_external: bool) -> None:
        """Feed one awake step into anticipation/Mysterium bookkeeping."""
        score = self.anticipation.observe_actual(result)
        self.anticipation.predict({"suggested_action":
                                   result.get("suggested_action")})
        if is_external:
            self.controller.note_stimulus()
        else:
            self.controller.note_silence()
        if score is not None:
            # An absence is novel only while absences are still rare;
            # routine silence is a pattern, not the unknown.
            history = self.anticipation._absence_history[-50:]
            absence_rate = (sum(history) / len(history)) if history else 0.0
            novel_absence = result.get("is_absence") and absence_rate < 0.3
            self.mysterium.update({
                "prediction_hit": score["hit"],
                "prediction_miss_streak": self.anticipation.miss_streak,
                "novelty": 1.0 if novel_absence else 0.0,
                "stable_patterns": score["hit"]
                and self.anticipation.miss_streak == 0
                and self.anticipation.rolling_accuracy() > 0.8,
                "logos_fracture": float(result.get("logos_fracture", 0.0)
                                        or 0.0),
            })

    # -- the latent sequence ----------------------------------------------------------

    def _context(self, silence: int, **extra: Any) -> Dict[str, Any]:
        context = {
            "silence_duration": silence,
            "trace_length": len(self.bridge.trace),
            "unknown_pressure": self.mysterium.pressure,
            "latent_max_steps": self.max_cycle_steps,
            "consolidated_recently": self._consolidated_recently,
            "replayed_recently": self._replayed_recently,
        }
        context.update(extra)
        return context

    def maybe_cycle(self, step: int, silence: int,
                    **extra: Any) -> Optional[Dict[str, Any]]:
        """Ask the scheduler; run one bounded latent sequence if it says so.

        Returns the wake summary dict when a cycle ran, else ``None``.
        """
        context = self._context(silence, **extra)
        decision = self.scheduler.evaluate(context)
        if decision.decision == LatentDecision.ENTER_QUIET:
            if self.controller.can_transition(LatentMode.QUIET):
                self.controller.transition(LatentMode.QUIET,
                                           decision.reason, step)
            return None
        if decision.decision != LatentDecision.ENTER_SLEEP:
            if decision.decision == LatentDecision.CONTINUE_AWAKE \
                    and self.controller.mode == LatentMode.QUIET \
                    and silence == 0:
                self.controller.transition(LatentMode.AWAKE,
                                           "input resumed", step)
            return None

        # One bounded latent sequence; each transition is safety-checked.
        started = time.time()
        summary: Dict[str, Any] = {"step": step, "cycles": []}
        transition = self.controller.transition(LatentMode.SLEEP,
                                                decision.reason, step)
        check = self.safety.validate_mode_transition(
            transition, {"max_steps": decision.max_steps, **context})
        if not check.safe:
            self.controller.wake({"refused": check.violations},
                                 "latent safety refused the cycle", step)
            return None

        if self.scheduler.should_enter_consolidation(context):
            self.controller.transition(LatentMode.CONSOLIDATION,
                                       "consolidation due", step)
            result = self.sleep_cycle.run(decision.max_steps, context)
            self.controller.note_consolidation()
            self._consolidated_recently = True
            self.mysterium.update({"consolidated": True})
            summary["cycles"].append({"type": "consolidation",
                                      **result.to_dict()})
            self.controller.transition(LatentMode.REPLAY
                                       if self.scheduler.should_enter_replay(
                                           self._context(silence, **extra))
                                       else LatentMode.WAKE_TRANSITION,
                                       "consolidation complete", step)
        elif self.controller.mode == LatentMode.SLEEP:
            # A plain sleep pass still settles activity and heartbeats.
            result = self.sleep_cycle.run(max(1, decision.max_steps // 5),
                                          context)
            summary["cycles"].append({"type": "sleep", **result.to_dict()})
            if self.scheduler.should_enter_replay(context):
                self.controller.transition(LatentMode.REPLAY,
                                           "replay due", step)

        if self.controller.mode == LatentMode.REPLAY:
            dream_context = {"strategy": extra.get("strategy", "recent"),
                             "plasticity_engine": self.plasticity_engine,
                             "run_id": extra.get("run_id", "")}
            if self.mysterium.pressure >= self.scheduler.dream_unknown_pressure:
                self.controller.transition(LatentMode.DREAM,
                                           "unknown pressure elevated", step)
            result = self.dream_cycle.run(decision.max_steps, dream_context)
            self.controller.note_replay()
            self._replayed_recently = True
            summary["cycles"].append({
                "type": ("dream" if self.controller.mode == LatentMode.DREAM
                         else "replay"),
                **result.to_dict()})

        summary["duration_s"] = round(time.time() - started, 6)
        summary["mysterium_pressure"] = round(self.mysterium.pressure, 4)
        summary["anticipation_accuracy"] = round(
            self.anticipation.rolling_accuracy(), 4)
        self.controller.wake(summary, "latent sequence complete", step)
        self.cycle_log.append({"step": step,
                               "cycles": [c["type"]
                                          for c in summary["cycles"]]})
        # Eligibility cools down until new input/trace accumulates.
        self._consolidated_recently = True
        self._replayed_recently = True
        return summary

    def reset_cooldowns(self) -> None:
        """New external input arrived: latent work becomes due again."""
        self._consolidated_recently = False
        self._replayed_recently = False

    # -- complexity (periodic, cheap) -------------------------------------------------

    def evaluate_complexity(self) -> Dict[str, Any]:
        recent = self.bridge.trace.recent(50)
        actions = [r.data.get("action") for r in recent
                   if r.category == "action"]
        kinds = [r.data.get("kind") for r in recent if r.category == "event"]
        reading = self.complexity.evaluate({
            "recent_actions": [a for a in actions if a],
            "recent_signal_kinds": [k for k in kinds if k],
            "state_norm": self.bridge.substrate_state_norm(),
            "activity_rate": self.bridge.substrate.metrics().activity_rate,
            "habit_weights": dict(self.bridge.habit.weights),
        })
        return reading.to_dict()

    # -- reporting / status ---------------------------------------------------------------

    def build_report(self) -> LatentReportBuilder:
        return LatentReportBuilder().collect(
            controller=self.controller, sleep_cycle=self.sleep_cycle,
            dream_cycle=self.dream_cycle, replay_engine=self.replay_engine,
            anticipation=self.anticipation, mysterium=self.mysterium,
            complexity=self.complexity, store=self.store,
            safety=self.safety, scheduler=self.scheduler)

    def save_report(self, json_path: Union[str, Path],
                    md_path: Union[str, Path]) -> Dict[str, Any]:
        self._last_report_paths = self.build_report().save(json_path,
                                                           md_path)
        return self._last_report_paths

    def summary(self) -> Dict[str, Any]:
        """Compact latent status for the Inner MAP / supervisor."""
        store = self.store.snapshot()
        counts = self.controller.counts
        return {
            "enabled": True,
            "mode": self.controller.mode,
            "mode_duration_s": round(self.controller.state.mode_duration_s(),
                                     3),
            "last_transition": (self.controller.history[-1].to_dict()
                                if self.controller.history else None),
            "sleep_cycle_count": self.sleep_cycle.cycles_run,
            "dream_cycle_count": self.dream_cycle.cycles_run,
            "replay_count": store["replay_count"],
            "counterfactual_count": store["dream_count"],
            "anticipation_accuracy": round(
                self.anticipation.rolling_accuracy(), 4),
            "mysterium_pressure": round(self.mysterium.pressure, 4),
            "mysterium_reasons": [r["reason"] for r in
                                  self.mysterium.reasons[-3:]],
            "complexity_pressure": (self.complexity.history[-1]
                                    if self.complexity.history else None),
            "consolidated_schema_count": store["schema_count"],
            "latent_safety_status": ("ok" if self.safety.rejected_count == 0
                                     else f"{self.safety.rejected_count} "
                                          "rejected"),
            "latent_report_path": (self._last_report_paths or {}).get(
                "markdown"),
            "dream_trace_count": store["dream_count"],
            "external_actions_during_latent": 0,  # structurally
            "mode_counts": dict(counts),
        }
