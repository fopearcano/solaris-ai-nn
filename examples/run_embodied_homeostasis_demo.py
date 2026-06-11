#!/usr/bin/env python3
"""Embodied homeostasis demo: energy, danger, and reward in the GridWorld.

    python examples/run_embodied_homeostasis_demo.py --steps 300

The body spends energy, meets reward/danger markers, and gets blocked by
walls; the regulator turns that into need pressure (restore_energy,
avoid_danger, approach_reward, respect_boundary) and biased suggestions.
Simulation-only throughout.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embodied homeostasis demo (simulation-only)")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/embodied_homeostasis")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    runner = SensorimotorSimulationRunner(
        max_steps=args.steps, seed=args.seed, state_dir=args.state_dir,
        enable_homeostasis=True, homeostasis_update_interval_steps=10)
    runner.run()
    regulator = runner.homeostasis
    summary = regulator.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- embodied homeostasis demo")
    print("=" * 70)
    print(f"steps:               {runner.steps_run} "
          f"(rewards {runner.rewards_consumed}, "
          f"collisions {runner.collisions}, "
          f"exhaustion events {runner.body.energy.exhaustion_events})")
    print(f"final energy:        {runner.body.energy.energy:.1f}/"
          f"{runner.body.energy.max_energy:.0f}")
    print(f"regulation updates:  {summary['updates']}")
    print(f"dominant need:       {summary['dominant_need']}")
    print(f"dominant drive:      {summary['dominant_drive']}")
    print(f"valence (rolling):   {regulator.valence.rolling()}")
    print(f"best desire:         {summary['best_desire']}")
    print()
    print("variables (most urgent):")
    for variable in regulator.state.most_urgent(5):
        print(f"  {variable.name:24s} value={variable.value:.2f} "
              f"urgency={variable.urgency:.2f} ({variable.trend})")
    print()
    result = regulator.last_result
    if result and result.conflicts:
        print("conflicts resolved (safety-first ladder):")
        for conflict in result.conflicts[:3]:
            print(f"  {conflict.kind}: -> {conflict.winner} "
                  f"(rule {conflict.resolution_rule})")
    suppressed = [c for c in (result.desire_candidates if result else [])
                  if c.blocked]
    for candidate in suppressed[:3]:
        print(f"suppressed: {candidate.proposal} -- "
              f"{candidate.blocked_reason[:70]}")
    print()
    print("note: needs are pressure estimates; suggestions stay "
          "simulation-only and execute nothing by themselves.")


if __name__ == "__main__":
    main()
