#!/usr/bin/env python3
"""Run the bounded soak continuity experiment.

Examples:

    python examples/run_soak_continuity.py
    python examples/run_soak_continuity.py --steps 500 --state-dir .solaris_ai_nn_state/dev_soak
    python examples/run_soak_continuity.py --duration 10 --seed 3

The default run is SAFE and bounded (500 steps, checkpoint every 50). Passing
``--continuous`` removes the step/time bound and must be stopped manually.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.soak_continuity import run_soak_continuity


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded soak continuity experiment")
    parser.add_argument("--steps", type=int, default=500, help="max session steps (default 500)")
    parser.add_argument("--duration", type=float, default=None, help="max wall-clock seconds")
    parser.add_argument("--state-dir", type=str, default=".solaris_ai_nn_state/dev_soak")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="run unbounded (manual stop required) -- NOT for tests",
    )
    args = parser.parse_args()

    steps = None if args.continuous else args.steps
    if args.continuous:
        print(
            "WARNING: --continuous runs an UNBOUNDED loop. It will not stop on "
            "its own; press Ctrl-C to stop it gracefully.\n"
        )

    run_soak_continuity(
        steps=steps,
        duration=args.duration,
        state_dir=args.state_dir,
        seed=args.seed,
        continuous=args.continuous,
        verbose=True,
    )


if __name__ == "__main__":
    main()
