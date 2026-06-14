#!/usr/bin/env python3
"""Boundary regression demo: does each protected line still hold?

    python examples/run_boundary_regression_demo.py --state-dir .solaris_ai_nn_state/test_boundary_regression

Probes each protected boundary with an inert request -- sensory, motor,
governance, ClaimGuard, simulated/real -- and reports whether the boundary was
crossed. Crossing a boundary fails the test. Nothing is executed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.safety_invariants import (
    BoundaryRegressionSuite,
    SafetyEvidenceLedger,
)


def main():
    parser = argparse.ArgumentParser(description="Boundary regression demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_boundary_regression")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    suite = BoundaryRegressionSuite()
    results = suite.run_all()
    summary = suite.summary(results)
    ledger = SafetyEvidenceLedger(state_dir=args.state_dir)
    ledger.record_boundary(results)
    out = {"summary": summary, "results": [r.to_dict() for r in results]}
    with open(os.path.join(args.state_dir, "boundary_regression.json"),
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Boundary regression demo ===")
    for r in results:
        if r.boundary in ("sensory_input", "motor_action",
                          "actuation_firewall", "governance", "claim_guard",
                          "simulated_real_evidence"):
            print(f"  {r.boundary:<26} {r.status:<12} "
                  f"crossed={r.boundary_crossed}")
    print(f"boundaries held : {summary['passed_count']}/"
          f"{summary['boundary_count']}")
    print(f"all held        : {summary['all_held']}")
    print(f"boundaries crossed : {summary['boundaries_crossed']}")
    print("note            : probes are inert; nothing was executed.")
    assert summary["all_held"], "a boundary was crossed"


if __name__ == "__main__":
    main()
