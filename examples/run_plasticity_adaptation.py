#!/usr/bin/env python3
"""Plasticity adaptation experiment (feedback inversion).

Examples:

    python examples/run_plasticity_adaptation.py --enable-plasticity --steps 500
    python examples/run_plasticity_adaptation.py --dry-run --steps 300
    python examples/run_plasticity_adaptation.py --rollback-last

The reward rule flips at the midpoint; with plasticity enabled the engine tunes
runtime parameters (bounded, validated, logged, rollbackable) to re-adapt.
``--rollback-last`` loads the persisted brain and undoes the last applied step.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.plasticity_adaptation import (
    rollback_last,
    run_plasticity_adaptation,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plasticity adaptation experiment")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--state-dir", type=str, default=".solaris_ai_nn_state/plasticity_demo")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true", help="log proposals but do not apply")
    parser.add_argument("--enable-plasticity", action="store_true",
                        help="enable applying plasticity (default off unless --dry-run)")
    parser.add_argument("--rollback-last", action="store_true",
                        help="load state and roll back the last applied plasticity step")
    args = parser.parse_args()

    if args.rollback_last:
        rollback_last(state_dir=args.state_dir, seed=args.seed, verbose=True)
        return

    # Plasticity is applied when --enable-plasticity is set, or proposed-only in --dry-run.
    enable = args.enable_plasticity or args.dry_run
    run_plasticity_adaptation(
        steps=args.steps, state_dir=args.state_dir, seed=args.seed,
        enable_plasticity=enable, dry_run=args.dry_run, verbose=True,
    )


if __name__ == "__main__":
    main()
