"""Minimal continuous-ESN experiment.

The smallest end-to-end demonstration of the Solaris-AI-NN bet:

    long-running weak adaptation > expensive one-shot intelligence

A tiny world repeatedly presents a handful of stimulus patterns, each with one
"correct" response. The loop starts knowing nothing (all readout weights zero,
so it always picks the first action). Through cheap online updates -- one per
event -- it gradually learns to pick the right action for each pattern, habit
biases for rewarded pathways grow, and periodic synthesis prunes the weak
weights left behind.

Nothing here is intelligent in any strong sense. It is a *continuous cognition
prototype*: observe the metrics, not the metaphor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..runtime.experiment_loop import ExperimentLoop
from ..signals import canonical as C
from ..signals.encoding import EventEncoder

# A tiny fixed world: stimulus payload -> the single correct action.
WORLD: Dict[str, str] = {
    "light": "approach",
    "noise": "withdraw",
    "food": "consume",
}
ACTIONS: List[str] = ["approach", "withdraw", "consume"]


@dataclass
class RepeatedPatternEnvironment:
    """Cycles through stimulus patterns and rewards correct actions.

    Reward is +1 when the loop's action matches the correct response for the
    current stimulus, -1 otherwise. Every ``silence_period`` steps it emits no
    stimulus, letting the loop's heartbeat / absence dynamics run.

    It also records correctness so the experiment can compare *early* vs *late*
    accuracy -- the concrete evidence that behaviour changed over time.
    """

    silence_period: int = 7
    patterns: List[str] = field(default_factory=lambda: list(WORLD.keys()))
    history: List[int] = field(default_factory=list)  # 1 correct, 0 wrong
    _i: int = 0

    def next_stimulus(self, step: int) -> Optional[C.Stimulus]:
        if self.silence_period > 0 and step % self.silence_period == 0:
            return None  # a beat of silence
        payload = self.patterns[self._i % len(self.patterns)]
        self._i += 1
        intensity = 0.5 + 0.5 * ((step % 3) / 2.0)  # mild variation
        return C.Stimulus(origin="world", modality="sensor", payload=payload, intensity=intensity)

    def react(self, stimulus: Optional[C.Stimulus], action: C.Action) -> Optional[float]:
        if stimulus is None or stimulus.is_absence:
            return None  # nothing to grade on a silent / self-generated beat
        correct = WORLD.get(str(stimulus.payload))
        if correct is None:
            return None
        hit = 1 if action.name == correct else 0
        self.history.append(hit)
        return 1.0 if hit else -1.0

    def accuracy(self, lo: float, hi: float) -> float:
        """Accuracy over the fractional window [lo, hi] of graded events."""
        if not self.history:
            return 0.0
        n = len(self.history)
        window = self.history[int(lo * n) : max(int(hi * n), int(lo * n) + 1)]
        return sum(window) / len(window) if window else 0.0


@dataclass
class ExperimentResult:
    """Outcome bundle returned by :func:`run_minimal_continuous_esn`."""

    telemetry_report: Dict[str, object]
    early_accuracy: float
    late_accuracy: float
    habit_pathways: int
    strong_habits: int
    pruned_pathways: int
    readout_nonzero: int


def run_minimal_continuous_esn(
    max_steps: int = 1500,
    seed: int = 7,
    verbose: bool = False,
) -> ExperimentResult:
    """Run the minimal continuous-ESN experiment and return its result.

    Args:
        max_steps: Number of loop steps (bounded; never infinite).
        seed: Determinism seed for the reservoir.
        verbose: If True, print a human-readable summary.
    """
    env = RepeatedPatternEnvironment()
    # Give the world's known stimuli distinct, collision-free encoder slots.
    encoder = EventEncoder(vocabulary=list(WORLD.keys()) + ["I exist!"])
    loop = ExperimentLoop(
        action_labels=ACTIONS,
        encoder=encoder,
        silence_steps=5,
        prune_every=300,
        snapshot_every=50,
        seed=seed,
    )
    # A brisk (but still stable, thanks to NLMS) rate keeps adaptation visible.
    loop.learner.lr = 0.5
    # Prune genuinely weak readout weights so the subtraction report is non-empty.
    loop.synthesis.readout_threshold = 0.005

    loop.run(max_steps, environment=env)

    result = ExperimentResult(
        telemetry_report=loop.telemetry.report(),
        early_accuracy=env.accuracy(0.0, 0.2),
        late_accuracy=env.accuracy(0.8, 1.0),
        habit_pathways=len(loop.habit.weights),
        strong_habits=loop.habit.strong_count(),
        pruned_pathways=loop.telemetry.pruned_pathways,
        readout_nonzero=loop.readout.nonzero_count(),
    )

    if verbose:
        print("=" * 60)
        print("Solaris-AI-NN -- minimal continuous-ESN experiment")
        print("=" * 60)
        print(loop.telemetry)
        print("-" * 60)
        print(f"early accuracy (first 20% of graded events): {result.early_accuracy:.2%}")
        print(f"late  accuracy (last 20% of graded events):  {result.late_accuracy:.2%}")
        print(f"habit pathways learned: {result.habit_pathways} "
              f"(strong: {result.strong_habits})")
        print(f"synthesis subtracted pathways: {result.pruned_pathways}")
        print(f"readout non-zero weights remaining: {result.readout_nonzero}")
        print("-" * 60)
        print("Interpretation: behaviour changed through cheap online updates,")
        print("habit reinforced rewarded pathways, synthesis subtracted weak ones.")
        print("No claim of consciousness -- only observable, low-compute adaptation.")

    return result


def main() -> None:
    """Console entry point (``solaris-nn-demo``)."""
    run_minimal_continuous_esn(verbose=True)


if __name__ == "__main__":
    main()
