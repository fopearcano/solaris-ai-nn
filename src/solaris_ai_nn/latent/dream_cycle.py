"""DreamCycle -- sandboxed replay and counterfactual simulation. Offline.

"Dream" is the engineering name for: take remembered windows, replay them
into an isolated copy of the bridge, generate labelled counterfactual
variants, replay those into a second sandbox, and measure how behaviour
diverges. No subjective experience is implied, nothing reaches the outside
world, and production state is untouched unless governance explicitly
allowed latent plasticity (default: dry-run, sandbox-only).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .anticipation import AnticipationTracker
from .counterfactual import COUNTERFACTUAL_KINDS, CounterfactualGenerator
from .latent_memory import DreamTrace, LatentMemoryRecord, LatentMemoryStore
from .mysterium import MysteriumTracker
from .offline_replay import OfflineReplayEngine, make_sandbox_bridge
from .safety import LatentSafetyValidator


@dataclass
class DreamCycleResult:
    """What one dream cycle simulated, and what diverged."""

    windows_replayed: int = 0
    events_replayed: int = 0
    counterfactuals_tested: int = 0
    counterfactual_kinds: List[str] = field(default_factory=list)
    mean_divergence: float = 0.0
    suggestion_divergences: int = 0
    offline_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    production_mutations: int = 0
    safety_rejections: int = 0
    dream_traces: List[Dict[str, Any]] = field(default_factory=list)
    offline: bool = True
    simulated: bool = True
    duration_s: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DreamCycle:
    """Bounded offline replay + counterfactual simulation."""

    bridge: Any  # SolarisNeuralBridge (production; only read by default)
    store: Optional[LatentMemoryStore] = None
    replay_engine: Optional[OfflineReplayEngine] = None
    generator: CounterfactualGenerator = field(
        default_factory=CounterfactualGenerator)
    anticipation: Optional[AnticipationTracker] = None
    mysterium: Optional[MysteriumTracker] = None
    safety: LatentSafetyValidator = field(
        default_factory=LatentSafetyValidator)
    governance: Any = None
    allow_production_mutation: bool = False
    seed: int = 0

    cycles_run: int = field(default=0, init=False)
    last_result: Optional[DreamCycleResult] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.replay_engine is None:
            self.replay_engine = OfflineReplayEngine(seed=self.seed)

    def run(self, max_steps: int,
            context: Optional[Dict[str, Any]] = None) -> DreamCycleResult:
        """One bounded dream cycle (``max_steps`` caps replayed events)."""
        if not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError("a dream cycle requires a positive bounded "
                             "max_steps")
        ctx = context or {}
        started = time.time()
        result = DreamCycleResult()

        strategy = ctx.get("strategy", "recent")
        window_size = min(int(ctx.get("window_size", 8)), max_steps)
        windows = self.replay_engine.select_windows(
            self.bridge.trace, strategy=strategy,
            window_size=window_size, count=int(ctx.get("window_count", 2)))

        events_budget = max_steps
        divergences: List[float] = []
        for index, window in enumerate(windows):
            if events_budget <= 0:
                break
            window["rows"] = window["rows"][:events_budget]

            # 1. Replay the remembered window into sandbox A (learning on:
            #    the sandbox may adapt; production does not).
            sandbox_a = make_sandbox_bridge(self.bridge)
            original = self.replay_engine.replay_window(
                window, sandbox_a, mutate=True)
            events_budget -= original["events_replayed"]
            result.windows_replayed += 1
            result.events_replayed += original["events_replayed"]

            # 2. A labelled counterfactual variant into sandbox B.
            kind = ctx.get("counterfactual_kind") or COUNTERFACTUAL_KINDS[
                (self.seed + index) % len(COUNTERFACTUAL_KINDS)]
            counterfactual = self.generator.generate(window, kind,
                                                     seed=self.seed + index)
            check = self.generator.validate(counterfactual)
            if not check.safe:
                result.safety_rejections += 1
                continue
            sandbox_b = make_sandbox_bridge(self.bridge)
            altered = self.replay_engine.replay_window(
                {**window, "rows": counterfactual["rows"],
                 "window_id": counterfactual["counterfactual_id"],
                 "strategy": f"counterfactual:{kind}"},
                sandbox_b, mutate=True)
            result.counterfactuals_tested += 1
            result.counterfactual_kinds.append(kind)

            # 3. Divergence between the remembered and the altered path.
            divergence = self._divergence(original, altered)
            divergences.append(divergence["score"])
            if divergence["suggestion_diverged"]:
                result.suggestion_divergences += 1

            trace = DreamTrace(
                window_id=str(window["window_id"]),
                counterfactual_kind=kind,
                counterfactual_id=counterfactual["counterfactual_id"],
                events_replayed=altered["events_replayed"],
                divergence=divergence,
                description=self.generator.describe(counterfactual))
            result.dream_traces.append(trace.to_dict())
            if self.store is not None:
                self.store.record_dream(trace)
                self.store.record_replay(self._replay_trace(original))

        result.mean_divergence = (round(sum(divergences) / len(divergences),
                                        6) if divergences else 0.0)

        # 4. Optional dry-run plasticity proposals (recorded, never applied).
        engine = ctx.get("plasticity_engine")
        if engine is not None:
            try:
                for step in engine.propose():
                    result.offline_suggestions.append({
                        "target": step.target.label(),
                        "new_value": step.change.new_value,
                        "reason": step.reason,
                        "offline": True, "applied": False})
            except Exception:  # proposals are best-effort
                pass

        # 5. Production mutation: gated twice (flag + governance), default no.
        if ctx.get("apply_to_production") and windows:
            mutation_check = self.safety.validate_production_mutation(
                {"component": "readout", "parameter": "learning_replay",
                 "new_value": "replay_learning"},
                {"latent_plasticity_allowed": self.allow_production_mutation,
                 "governance": self.governance,
                 "run_id": ctx.get("run_id", "")})
            if mutation_check.safe:
                replayed = self.replay_engine.replay_window(
                    windows[0], self.bridge, mutate=True)
                result.production_mutations += 1
                result.events_replayed += replayed["events_replayed"]
            else:
                result.safety_rejections += 1

        # 6. Feed the trackers.
        if self.mysterium is not None:
            self.mysterium.update({
                "counterfactual_divergence": result.mean_divergence,
                "replay_reproduced": result.windows_replayed > 0
                and result.mean_divergence < 0.9})
        if self.anticipation is not None and result.dream_traces:
            self.anticipation.observe_actual({
                "kind": "DreamReplay", "is_absence": False,
                "state_norm": self.bridge.substrate_state_norm()})

        result.duration_s = round(time.time() - started, 6)
        self.cycles_run += 1
        self.last_result = result
        if self.store is not None:
            self.store.record_cycle(LatentMemoryRecord(
                cycle_type="dream", steps_run=result.events_replayed,
                replayed_window_ids=[str(w["window_id"]) for w in windows],
                counterfactual_kinds=list(result.counterfactual_kinds),
                substrate_response={"mean_divergence":
                                    result.mean_divergence},
                offline_suggestions=result.offline_suggestions,
                production_mutated=result.production_mutations > 0,
                mysterium_change=result.mean_divergence * 0.04))
        return result

    @staticmethod
    def _divergence(original: Dict[str, Any],
                    altered: Dict[str, Any]) -> Dict[str, Any]:
        a, b = original["after"], altered["after"]
        norm_gap = abs(a["state_norm"] - b["state_norm"])
        confidence_gap = abs(a["confidence"] - b["confidence"])
        suggestion_diverged = a["suggested_action"] != b["suggested_action"]
        score = min(1.0, norm_gap / 5.0 + confidence_gap
                    + (0.5 if suggestion_diverged else 0.0))
        return {"score": round(score, 6),
                "state_norm_gap": round(norm_gap, 6),
                "confidence_gap": round(confidence_gap, 6),
                "suggestion_diverged": suggestion_diverged,
                "offline": True}

    @staticmethod
    def _replay_trace(outcome: Dict[str, Any]):
        from .latent_memory import ReplayTrace

        return ReplayTrace(
            window_id=str(outcome.get("window_id")),
            strategy=str(outcome.get("strategy")),
            events_replayed=int(outcome.get("events_replayed", 0)),
            before=outcome.get("before", {}), after=outcome.get("after", {}),
            comparison=outcome.get("comparison", {}),
            mutated_production=False)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "cycles_run": self.cycles_run,
            "allow_production_mutation": self.allow_production_mutation,
            "last_result": (self.last_result.to_dict()
                            if self.last_result else None),
        }
