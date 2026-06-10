#!/usr/bin/env python3
"""Run the bounded sidecar observation experiment (fake Solaris runtime).

    python examples/run_solaris_sidecar_observation.py
    python examples/run_solaris_sidecar_observation.py --steps 120 --publish
    python examples/run_solaris_sidecar_observation.py --state-dir .solaris_ai_nn_state/sidecar
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.solaris_sidecar_observation import run_sidecar_observation


def main() -> None:
    parser = argparse.ArgumentParser(description="Sidecar observation experiment")
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--state-dir", type=str, default=None,
                        help="optional dir for integration_state.json + JSONL exports")
    parser.add_argument("--publish", action="store_true",
                        help="leave observe-only mode")
    args = parser.parse_args()
    run_sidecar_observation(
        steps=args.steps, observe_only=not args.publish, seed=args.seed,
        state_dir=args.state_dir, verbose=True,
    )


if __name__ == "__main__":
    main()
