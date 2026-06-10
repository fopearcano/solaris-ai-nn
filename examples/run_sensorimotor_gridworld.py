#!/usr/bin/env python3
"""Run the bounded sensorimotor GridWorld experiment (simulation-only).

    python examples/run_sensorimotor_gridworld.py --steps 300
    python examples/run_sensorimotor_gridworld.py --substrate spiking_recurrent
    python examples/run_sensorimotor_gridworld.py --observe-only --steps 150
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.sensorimotor_gridworld import run_sensorimotor_gridworld


def main() -> None:
    parser = argparse.ArgumentParser(description="Sensorimotor GridWorld experiment")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--substrate", type=str, default="esn",
                        choices=["esn", "liquid_state", "spiking_recurrent"])
    parser.add_argument("--observe-only", action="store_true",
                        help="perceive + learn substrate state, never act")
    parser.add_argument("--enable-plasticity", action="store_true")
    parser.add_argument("--width", type=int, default=9)
    parser.add_argument("--height", type=int, default=7)
    args = parser.parse_args()
    run_sensorimotor_gridworld(
        steps=args.steps, state_dir=args.state_dir, seed=args.seed,
        substrate=args.substrate, observe_only=args.observe_only,
        enable_plasticity=args.enable_plasticity,
        width=args.width, height=args.height, verbose=True,
    )


if __name__ == "__main__":
    main()
