#!/usr/bin/env python3
"""Counterfactual dream demo over embodied reward/danger traces.

    python examples/run_counterfactual_dream_demo.py --steps 200

A bounded GridWorld session builds real reward/danger experience; then a
dream cycle replays remembered windows into sandboxes and tests labelled
counterfactual variants (e.g. reward swapped for danger). No simulated
action executes during the dream, production state is untouched, and the
report is ClaimGuard-scanned.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)
from solaris_ai_nn.latent import (
    CounterfactualGenerator,
    DreamCycle,
    LatentMemoryStore,
    LatentReportBuilder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Counterfactual dream demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/counterfactual_dream")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    # 1. Real (simulated-world) experience: reward/danger in the GridWorld.
    runner = SensorimotorSimulationRunner(
        max_steps=args.steps, seed=args.seed, state_dir=args.state_dir)
    runner.run()
    bridge = runner.bridge
    actions_after_run = len(runner.action_history)
    steps_before_dream = bridge.telemetry.steps

    # 2. The dream cycle: sandboxed replay + counterfactual variants.
    store = LatentMemoryStore(args.state_dir)
    dream = DreamCycle(bridge=bridge, store=store, seed=args.seed)
    result = dream.run(40, {"strategy": "high_valence", "window_count": 2,
                            "counterfactual_kind": "swap_reward_danger"})

    print("=" * 70)
    print("Solaris-AI-NN -- counterfactual dream demo (offline, sandboxed)")
    print("=" * 70)
    print(f"embodied steps:        {runner.steps_run} "
          f"(rewards {runner.rewards_consumed}, "
          f"collisions {runner.collisions})")
    print(f"windows replayed:      {result.windows_replayed}")
    print(f"counterfactuals:       {result.counterfactuals_tested} "
          f"({', '.join(result.counterfactual_kinds)})")
    print(f"mean divergence:       {result.mean_divergence}")
    print(f"suggestion diverged:   {result.suggestion_divergences} window(s)")
    print(f"production mutations:  {result.production_mutations} (default 0)")
    print(f"actions during dream:  "
          f"{len(runner.action_history) - actions_after_run} "
          "(no real action)")
    print(f"production untouched:  "
          f"{bridge.telemetry.steps == steps_before_dream}")
    for trace in result.dream_traces[:2]:
        print(f"  dream trace: {trace['description'][:90]}")

    # 3. Report (ClaimGuard scans before the Markdown is written).
    report = LatentReportBuilder(run_id="counterfactual-dream-demo").collect(
        dream_cycle=dream, replay_engine=dream.replay_engine, store=store)
    paths = report.save(Path(args.state_dir) / "latent_report.json",
                        Path(args.state_dir) / "latent_report.md")
    print(f"report:                {paths['markdown']} "
          f"(claim guard safe: {paths['claim_guard']['safe']})")


if __name__ == "__main__":
    main()
