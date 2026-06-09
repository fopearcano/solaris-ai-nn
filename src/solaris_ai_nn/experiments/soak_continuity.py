"""Soak continuity experiment -- a bounded long-running run with persistence.

Drives the :class:`ContinuousRunner` over a bounded number of steps while:

* injecting periodic external Stimulus events,
* leaving silence windows (so the runner synthesises continuity / absence
  stimuli and the substrate keeps evolving),
* producing `+1/-1` Reaction feedback (online learning + habit reinforcement),
* checkpointing periodically and running synthesis pruning occasionally,
* writing telemetry and a continuity log to a state directory.

It is the seed of the future 24-hour / 30-day soak tests, but it is always
bounded here (``max_steps`` and/or ``max_duration_s``); only an explicit
``continuous=True`` removes the bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..runtime import persistence as P
from ..runtime.continuous_runner import ContinuousRunner
from ..signals import canonical as C

WORLD: Dict[str, str] = {"light": "approach", "noise": "withdraw", "food": "consume"}
ACTIONS = ["approach", "withdraw", "consume"]


def _make_providers(period: int = 11, silence_len: int = 4):
    """Build (stimulus_provider, reaction_provider) for the tiny soak world."""
    payloads = list(WORLD.keys())

    def stimulus_provider(step: int) -> Optional[C.Stimulus]:
        # A silence window at the start of every `period` steps.
        if step % period < silence_len:
            return None
        payload = payloads[step % len(payloads)]
        return C.Stimulus(origin="world", modality="sensor", payload=payload, intensity=0.6)

    def reaction_provider(result: Dict[str, Any], stim: C.Stimulus) -> Optional[float]:
        correct = WORLD.get(str(stim.payload))
        if correct is None:
            return None
        return 1.0 if result["suggested_action"] == correct else -1.0

    return stimulus_provider, reaction_provider


@dataclass
class SoakResult:
    """Outcome of one soak run (mirrors the runner snapshot, plus paths)."""

    snapshot: Dict[str, Any]
    state_dir: str
    continuity_log_path: str
    continuity_events: int


def run_soak_continuity(
    steps: Optional[int] = 500,
    duration: Optional[float] = None,
    state_dir: str = ".solaris_ai_nn_state/dev_soak",
    seed: int = 7,
    checkpoint_interval: int = 50,
    prune_interval: int = 150,
    continuous: bool = False,
    verbose: bool = False,
) -> SoakResult:
    """Run a bounded soak session and return its result."""
    stimulus_provider, reaction_provider = _make_providers()
    runner = ContinuousRunner(
        state_dir=state_dir,
        max_steps=steps,
        max_duration_s=duration,
        heartbeat_interval_s=0.5,
        checkpoint_interval_steps=checkpoint_interval,
        prune_interval_steps=prune_interval,
        continuous=continuous,
        seed=seed,
        action_labels=ACTIONS,
        vocabulary=list(WORLD.keys()) + ["I exist!"],
        stimulus_provider=stimulus_provider,
        reaction_provider=reaction_provider,
        silence_threshold=3,
    )

    # Bracket the run with explicit soak markers in the continuity log.
    runner.continuity.log(P.SOAK_START, "soak session begin", lifetime_step=runner.lifetime_base)
    snapshot = runner.run()
    # The runner closed its continuity log on finalize; reopen (append) for the stop marker.
    closing = runner.pm.continuity_log(runner.run_id, runner.session_id)
    closing.log(P.SOAK_STOP, "soak session end", lifetime_step=snapshot["lifetime_steps"])
    closing.close()

    result = SoakResult(
        snapshot=snapshot,
        state_dir=str(runner.pm.state_dir),
        continuity_log_path=str(runner.pm.continuity_log_path),
        continuity_events=runner.pm.continuity_log().count(),
    )

    if verbose:
        print("=" * 60)
        print("Solaris-AI-NN -- soak continuity experiment")
        print("=" * 60)
        tele = snapshot["telemetry"]
        print(f"state dir:            {result.state_dir}")
        print(f"session steps:        {snapshot['session_steps']}")
        print(f"lifetime steps:       {snapshot['lifetime_steps']}")
        print(f"restart count:        {snapshot['restart_count']}")
        print(f"checkpoints:          {snapshot['checkpoints']}")
        print(f"pruning passes:       {snapshot['pruning_passes']}")
        print(f"habit pathways:       {snapshot['habit_pathways']}")
        print(f"reservoir norm:       {snapshot['reservoir_norm']:.4f}")
        print(f"recent pred. error:   {tele['recent_prediction_error']}")
        print(f"events/sec:           {tele['events_per_second']}")
        print(f"lifecycle state:      {snapshot['lifecycle']['state']}")
        print(f"continuity events:    {result.continuity_events}")
        print(f"continuity log:       {result.continuity_log_path}")
        print("-" * 60)
        print("Bounded soak complete; state checkpointed and continuity logged.")
        print("No claim of consciousness -- only observable, persistent adaptation.")

    return result


def main() -> None:
    run_soak_continuity(verbose=True)


if __name__ == "__main__":
    main()
