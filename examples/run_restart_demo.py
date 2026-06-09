#!/usr/bin/env python3
"""Restart recovery demo: run, persist, restart, and continue.

Examples:

    python examples/run_restart_demo.py
    python examples/run_restart_demo.py --state-dir .solaris_ai_nn_state/restart_demo
    python examples/run_restart_demo.py --simulate-crash

``--simulate-crash`` makes the first session leave ungraceful-shutdown metadata
(without killing the process), so the restart logs ``unexpected_death_detected``
and a ``brain_death_gap``.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.restart_recovery import run_restart_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Restart recovery demo")
    parser.add_argument("--state-dir", type=str, default=".solaris_ai_nn_state/restart_demo")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--steps", type=int, default=80, help="steps per session")
    parser.add_argument(
        "--simulate-crash",
        action="store_true",
        help="leave ungraceful-shutdown metadata so the restart detects a crash",
    )
    args = parser.parse_args()
    run_restart_demo(
        state_dir=args.state_dir,
        steps=args.steps,
        seed=args.seed,
        simulate_crash=args.simulate_crash,
        verbose=True,
    )


if __name__ == "__main__":
    main()
