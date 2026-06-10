#!/usr/bin/env python3
"""Run the embodied absence experiment (sparse world, long silences).

    python examples/run_embodied_absence.py --steps 300
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.embodied_absence import run_embodied_absence


def main() -> None:
    parser = argparse.ArgumentParser(description="Embodied absence experiment")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--substrate", type=str, default="esn",
                        choices=["esn", "liquid_state", "spiking_recurrent"])
    args = parser.parse_args()
    run_embodied_absence(steps=args.steps, state_dir=args.state_dir,
                         seed=args.seed, substrate=args.substrate, verbose=True)


if __name__ == "__main__":
    main()
