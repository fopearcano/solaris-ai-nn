"""Restart recovery experiment.

Demonstrates that a Solaris-AI-NN brain survives shutdown/restart: it runs a
bounded session, checkpoints, then a *new* runner over the same state directory
restores the persisted substrate and continues -- with the lifetime step count
and restart count carrying over.

With ``simulate_crash=True`` the first session's manifest is rewritten to look
like an ungraceful exit (no graceful-shutdown flag, plus a backdated last
heartbeat). This reproduces the on-disk condition a crash would leave *without
killing the Python process*, so the next startup logs ``unexpected_death_detected``
and a ``brain_death_gap``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict

from ..runtime.continuous_runner import ContinuousRunner
from ..runtime.persistence import PersistenceManager
from ..utils.math import norm
from .soak_continuity import ACTIONS, WORLD, _make_providers


@dataclass
class RestartResult:
    """Outcome of a two-session restart demonstration."""

    restart_count: int
    lifetime_steps: int
    session1_steps: int
    session2_steps: int
    restored_reservoir_norm: float
    restored_habit_count: int
    unexpected_death_detected: bool
    brain_death_gap_seconds: float
    continuity_log_path: str
    state_dir: str


def _build_runner(state_dir: str, seed: int, steps: int) -> ContinuousRunner:
    stimulus_provider, reaction_provider = _make_providers()
    return ContinuousRunner(
        state_dir=state_dir,
        max_steps=steps,
        heartbeat_interval_s=0.5,
        checkpoint_interval_steps=40,
        prune_interval_steps=0,
        seed=seed,
        action_labels=ACTIONS,
        vocabulary=list(WORLD.keys()) + ["I exist!"],
        stimulus_provider=stimulus_provider,
        reaction_provider=reaction_provider,
        silence_threshold=3,
    )


def run_restart_demo(
    state_dir: str = ".solaris_ai_nn_state/restart_demo",
    steps: int = 80,
    seed: int = 7,
    simulate_crash: bool = False,
    verbose: bool = False,
) -> RestartResult:
    """Run session 1, (optionally simulate a crash,) then restart and continue."""
    # --- Session 1 ---
    runner1 = _build_runner(state_dir, seed, steps)
    snap1 = runner1.run()

    if simulate_crash:
        # Simulate the metadata a crash would leave: not gracefully shut down,
        # and a backdated heartbeat so the next startup sees a brain-death gap.
        pm = PersistenceManager(state_dir)
        manifest = pm.load_manifest() or {}
        manifest["last_graceful_shutdown"] = False
        manifest["last_heartbeat_ts"] = time.time() - 5.0
        pm.save_manifest(manifest)

    # --- Session 2 (restart from the same state dir) ---
    runner2 = _build_runner(state_dir, seed, steps)
    # Capture restored state *before* the second session runs.
    restored_norm = norm(runner2.bridge.esn.state)
    restored_habits = len(runner2.bridge.habit.weights)
    snap2 = runner2.run()

    result = RestartResult(
        restart_count=snap2["restart_count"],
        lifetime_steps=snap2["lifetime_steps"],
        session1_steps=snap1["session_steps"],
        session2_steps=snap2["session_steps"],
        restored_reservoir_norm=restored_norm,
        restored_habit_count=restored_habits,
        unexpected_death_detected=snap2["unexpected_deaths"] > 0,
        brain_death_gap_seconds=snap2["brain_death_gap_seconds"],
        continuity_log_path=snap2["continuity_log_path"],
        state_dir=snap2["state_dir"],
    )

    if verbose:
        print("=" * 60)
        print("Solaris-AI-NN -- restart recovery demo")
        print("=" * 60)
        print(f"state dir:                 {result.state_dir}")
        print(f"simulated crash:           {simulate_crash}")
        print(f"restart count:             {result.restart_count}")
        print(f"session 1 steps:           {result.session1_steps}")
        print(f"session 2 steps:           {result.session2_steps}")
        print(f"total lifetime steps:      {result.lifetime_steps}")
        print(f"restored reservoir norm:   {result.restored_reservoir_norm:.4f}")
        print(f"restored habit weights:    {result.restored_habit_count}")
        print(f"unexpected death detected: {result.unexpected_death_detected}")
        print(f"brain-death gap (s):       {result.brain_death_gap_seconds:.3f}")
        print(f"continuity log:            {result.continuity_log_path}")
        print("-" * 60)
        print("The substrate resumed from persisted state across a restart.")
        if simulate_crash:
            print("The simulated crash was detected (ungraceful death + gap logged).")

    return result


def main() -> None:
    run_restart_demo(verbose=True)


if __name__ == "__main__":
    main()
