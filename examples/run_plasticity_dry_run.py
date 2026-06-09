#!/usr/bin/env python3
"""Plasticity dry-run: propose + validate mutations, but apply none.

Proves the safety story: with plasticity proposals enabled in dry-run mode, the
engine logs proposals and safety decisions, but no runtime parameter changes.
This script runs a short session and then confirms the key parameters are
unchanged from their initial values.

    python examples/run_plasticity_dry_run.py
    python examples/run_plasticity_dry_run.py --steps 200 --state-dir .solaris_ai_nn_state/dry
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.plasticity_adaptation import run_plasticity_adaptation


def main() -> None:
    parser = argparse.ArgumentParser(description="Plasticity dry-run")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str, default=".solaris_ai_nn_state/plasticity_dry_run")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    result = run_plasticity_adaptation(
        steps=args.steps, state_dir=args.state_dir, seed=args.seed,
        enable_plasticity=True, dry_run=True, verbose=True,
    )

    print("-" * 64)
    print("Dry-run verification:")
    print(f"  applied steps:                 {result.applied_count} (expected 0)")
    print(f"  learning rate unchanged:       "
          f"{result.learning_rate_before == result.learning_rate_after} "
          f"({result.learning_rate_before:.4f})")
    print(f"  exploration unchanged:         "
          f"{result.exploration_before == result.exploration_after} "
          f"({result.exploration_before:.4f})")
    audit_rows = result.snapshot.get("plasticity", {}).get("applied_count", 0)
    print(f"  parameters did NOT change -> proposals were logged, not applied.")


if __name__ == "__main__":
    main()
