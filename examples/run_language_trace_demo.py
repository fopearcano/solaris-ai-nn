#!/usr/bin/env python3
"""Run the language trace demo: the system describes a bounded session.

    python examples/run_language_trace_demo.py --steps 200
    python examples/run_language_trace_demo.py --embodied --steps 150
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.language_trace_demo import run_language_trace_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Language trace demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/language_demo")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--substrate", type=str, default="esn",
                        choices=["esn", "liquid_state", "spiking_recurrent"])
    parser.add_argument("--embodied", action="store_true",
                        help="run the sensorimotor GridWorld session instead")
    parser.add_argument("--enable-plasticity", action="store_true")
    args = parser.parse_args()
    run_language_trace_demo(
        steps=args.steps, state_dir=args.state_dir, seed=args.seed,
        substrate=args.substrate, embodied=args.embodied,
        enable_plasticity=args.enable_plasticity, verbose=True,
    )


if __name__ == "__main__":
    main()
