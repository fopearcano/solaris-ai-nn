#!/usr/bin/env python3
"""Do spiking-like substrates keep evolving through silence?

Examples:

    python examples/run_spiking_silence.py --steps 300
    python examples/run_spiking_silence.py --substrates spiking_recurrent
    python examples/run_spiking_silence.py --steps 150 --state-dir .solaris_ai_nn_state/silence

Three equal phases: external stimuli, silence (escalating "I exist!" absence
stimuli, AION-style), then stimuli again. Reports per-phase activity and whether
the substrate went inert. Always bounded.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.spiking_silence import run_spiking_silence


def main() -> None:
    parser = argparse.ArgumentParser(description="Spiking silence experiment")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str, default=None,
                        help="optional dir to save the report JSON")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--substrates", type=str, default="liquid_state,spiking_recurrent",
                        help="comma-separated substrate names")
    args = parser.parse_args()
    names = [s.strip() for s in args.substrates.split(",") if s.strip()]
    run_spiking_silence(
        steps=args.steps, seed=args.seed, substrates=names,
        state_dir=args.state_dir, verbose=True,
    )


if __name__ == "__main__":
    main()
