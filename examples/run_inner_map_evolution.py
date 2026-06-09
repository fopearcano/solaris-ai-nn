#!/usr/bin/env python3
"""Run the bounded Inner MAP evolution experiment.

Examples:

    python examples/run_inner_map_evolution.py
    python examples/run_inner_map_evolution.py --steps 300 --state-dir .solaris_ai_nn_state/inner_map_demo
    python examples/run_inner_map_evolution.py --steps 100 --seed 3

Always bounded by ``--steps``. Persists ``inner_map.json`` under the state dir and
prints a compact self-model report plus a Mermaid self-map preview.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.inner_map_evolution import run_inner_map_evolution


def main() -> None:
    parser = argparse.ArgumentParser(description="Inner MAP evolution experiment")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str, default=".solaris_ai_nn_state/inner_map_demo")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--checkpoint-interval", type=int, default=50)
    parser.add_argument("--inner-map-interval", type=int, default=10)
    args = parser.parse_args()
    run_inner_map_evolution(
        steps=args.steps,
        state_dir=args.state_dir,
        seed=args.seed,
        checkpoint_interval=args.checkpoint_interval,
        inner_map_update_interval=args.inner_map_interval,
        verbose=True,
    )


if __name__ == "__main__":
    main()
