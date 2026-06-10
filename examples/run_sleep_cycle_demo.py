#!/usr/bin/env python3
"""Sleep cycle demo: awake input -> silence -> sleep/consolidation -> wake.

    python examples/run_sleep_cycle_demo.py --steps 200

Shows the mode ladder explicitly: the controller's transitions are printed,
the consolidation distils habit pathways into schemas, and the wake
transition carries a summary back to the awake mode (and the Inner MAP).
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def main() -> None:
    parser = argparse.ArgumentParser(description="Sleep cycle demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/sleep_cycle_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    active = args.steps // 2

    def provider(step):
        if step <= active:
            return C.Stimulus(payload=["light", "noise"][step % 2],
                              intensity=0.6)
        return None

    def reaction(result, stim):
        return 1.0 if result["suggested_action"] == "approach" else -0.3

    runner = ContinuousRunner(
        state_dir=args.state_dir, max_steps=args.steps, seed=args.seed,
        vocabulary=["light", "noise"],
        stimulus_provider=provider, reaction_provider=reaction,
        enable_latent=True, latent_interval_steps=max(20, args.steps // 8),
        latent_max_steps=15)
    runner.run()
    latent = runner.latent

    print("=" * 70)
    print("Solaris-AI-NN -- sleep cycle demo")
    print("=" * 70)
    print(f"awake input for {active} steps, then silence\n")
    print("mode transitions (every one logged):")
    for t in latent.controller.history:
        print(f"  step {t.step:4d}  {t.from_mode:>15s} -> {t.to_mode:<15s} "
              f"({t.reason[:45]})")
    print()
    summary = latent.controller.last_wake_summary or {}
    print("wake transition summary:")
    print(f"  cycles run:        {[c['type'] for c in summary.get('cycles', [])]}")
    print(f"  unknown pressure:  {summary.get('mysterium_pressure')}")
    print(f"  anticipation acc.: {summary.get('anticipation_accuracy')}")
    print()
    print("consolidated schemas:")
    for schema in latent.store.schemas()[:5]:
        print(f"  - {schema.summary()}")
    if not latent.store.schemas():
        print("  (none: not enough repeated pathways yet)")
    print()
    print(f"sleep cycles:   {latent.sleep_cycle.cycles_run}")
    print(f"latent report:  {args.state_dir}/latent_report.md")
    print("note: 'sleep' here is bounded maintenance/consolidation, not "
          "human sleep.")


if __name__ == "__main__":
    main()
