#!/usr/bin/env python3
"""Bounded latent replay demo: input, then silence, then offline replay.

    python examples/run_latent_replay_demo.py --steps 200

The runner processes external stimuli for the first third of the run, goes
quiet, and the latent scheduler reacts: sleep, consolidation, offline replay
into sandboxes, and (if unknown pressure is elevated) a dream cycle. Dry-run
only -- no production mutation, no external actions, everything bounded.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def main() -> None:
    parser = argparse.ArgumentParser(description="Latent replay demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/latent_replay_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    active = args.steps // 3

    def provider(step):
        if step <= active:
            return C.Stimulus(payload=["light", "noise", "food"][step % 3],
                              intensity=0.5)
        return None  # silence: latent processing becomes due

    def reaction(result, stim):
        return 1.0 if result["suggested_action"] == "approach" else -0.5

    runner = ContinuousRunner(
        state_dir=args.state_dir, max_steps=args.steps, seed=args.seed,
        vocabulary=["light", "noise", "food"],
        stimulus_provider=provider, reaction_provider=reaction,
        enable_latent=True, latent_interval_steps=max(25, args.steps // 6),
        latent_max_steps=20, latent_dry_run=True)
    runner.run()
    latent = runner.snapshot()["latent"]

    print("=" * 70)
    print("Solaris-AI-NN -- latent replay demo (offline, dry-run)")
    print("=" * 70)
    print(f"steps:               {args.steps} ({active} with input, then "
          "silence)")
    print(f"mode now:            {latent['mode']}")
    print(f"mode counts:         {latent['mode_counts']}")
    print(f"sleep cycles:        {latent['sleep_cycle_count']}")
    print(f"dream cycles:        {latent['dream_cycle_count']}")
    print(f"replay windows:      {latent['replay_count']}")
    print(f"counterfactuals:     {latent['counterfactual_count']}")
    print(f"anticipation acc.:   {latent['anticipation_accuracy']}")
    print(f"unknown pressure:    {latent['mysterium_pressure']}")
    print(f"schemas:             {latent['consolidated_schema_count']}")
    print(f"production mutation: 0 (dry-run; structurally none)")
    print(f"latent report:       {latent['latent_report_path']}")
    md = Path(args.state_dir) / "latent_report.md"
    if md.exists():
        for line in md.read_text().splitlines():
            if "During offline replay" in line:
                print(f"explanation:         {line.strip()[:100]}")
                break


if __name__ == "__main__":
    main()
