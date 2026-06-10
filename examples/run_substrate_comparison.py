#!/usr/bin/env python3
"""Compare low-compute substrates on the same deterministic event trace.

Examples:

    python examples/run_substrate_comparison.py --steps 300
    python examples/run_substrate_comparison.py --substrates esn,liquid_state
    python examples/run_substrate_comparison.py --steps 150 --state-dir .solaris_ai_nn_state/cmp

Always bounded; never continuous. Prints a side-by-side metrics table.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.substrate_comparison import run_substrate_comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Substrate comparison experiment")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str, default=None,
                        help="optional dir to save the comparison report JSON")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--substrates", type=str,
                        default="esn,liquid_state,spiking_recurrent",
                        help="comma-separated substrate names")
    args = parser.parse_args()
    names = [s.strip() for s in args.substrates.split(",") if s.strip()]
    run_substrate_comparison(
        steps=args.steps, seed=args.seed, substrates=names,
        state_dir=args.state_dir, verbose=True,
    )


if __name__ == "__main__":
    main()
