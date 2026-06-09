"""Plasticity benchmarks -- compare configurations with simple metrics.

Lightweight, bounded comparisons (no heavy ML). The headline benchmark contrasts
a plasticity-enabled run against a plasticity-disabled run on the same
feedback-inversion world, so the effect of controlled self-modification is
visible as concrete numbers (applied steps, learning-rate drift, accuracy).

The runner is imported lazily inside functions to avoid an import cycle
(``runtime`` imports ``plasticity``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

WORLD = {"light": "approach", "noise": "withdraw", "food": "consume"}
FLIPPED = {"light": "withdraw", "noise": "consume", "food": "approach"}
ACTIONS = ["approach", "withdraw", "consume"]


def _providers(half: int):
    payloads = list(WORLD.keys())

    def stimulus_provider(step: int):
        from ..signals import canonical as C
        if step % 9 < 3:  # silence window
            return None
        return C.Stimulus(origin="world", modality="sensor",
                          payload=payloads[step % len(payloads)], intensity=0.6)

    def reaction_provider(result: Dict[str, Any], stim) -> Optional[float]:
        mapping = WORLD if result["step"] < half else FLIPPED
        correct = mapping.get(str(stim.payload))
        if correct is None:
            return None
        return 1.0 if result["suggested_action"] == correct else -1.0

    return stimulus_provider, reaction_provider


def _run_one(state_dir: str, steps: int, seed: int, enable_plasticity: bool) -> Dict[str, Any]:
    from ..runtime.continuous_runner import ContinuousRunner

    stimulus_provider, reaction_provider = _providers(steps // 2)
    runner = ContinuousRunner(
        state_dir=state_dir, max_steps=steps, checkpoint_interval_steps=max(25, steps // 4),
        prune_interval_steps=max(50, steps // 4), seed=seed, action_labels=ACTIONS,
        vocabulary=list(WORLD.keys()) + ["I exist!"],
        stimulus_provider=stimulus_provider, reaction_provider=reaction_provider,
        silence_threshold=3, enable_plasticity=enable_plasticity,
        plasticity_interval_steps=25,
    )
    snap = runner.run()
    eng = runner.plasticity_engine
    return {
        "applied": eng.applied_count if eng else 0,
        "rejected": eng.rejected_count if eng else 0,
        "learning_rate": runner.bridge.learner.lr,
        "exploration": runner.bridge.exploration,
        "recent_error": snap["telemetry"]["recent_prediction_error"],
        "habit_pathways": snap["habit_pathways"],
    }


@dataclass
class BenchmarkResult:
    with_plasticity: Dict[str, Any]
    without_plasticity: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"with_plasticity": self.with_plasticity,
                "without_plasticity": self.without_plasticity}


class PlasticityBenchmark:
    """Habit-vs-synthesis / plasticity-on-vs-off comparison."""

    def run(self, state_dir: str, steps: int = 200, seed: int = 7) -> BenchmarkResult:
        on = _run_one(f"{state_dir}/on", steps, seed, enable_plasticity=True)
        off = _run_one(f"{state_dir}/off", steps, seed, enable_plasticity=False)
        return BenchmarkResult(with_plasticity=on, without_plasticity=off)


def run_habit_vs_synthesis_benchmark(state_dir: str, steps: int = 200, seed: int = 7) -> Dict[str, Any]:
    """Convenience wrapper returning a plain-dict comparison."""
    return PlasticityBenchmark().run(state_dir, steps=steps, seed=seed).to_dict()
