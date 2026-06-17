#!/usr/bin/env python3
"""Membrane contracts demo: birth/observation/ontogenesis/semiogenesis/cognition.

    python examples/run_membrane_contracts_demo.py --state-dir .solaris_ai_nn_live/contracts_demo

Stages a clean pipeline and prints each downstream module's contract status toward the
membrane boundary.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.membrane_integration import MembraneIntegrationRuntime
from solaris_ai_nn.membrane_integration.downstream_contracts import summary
from run_membrane_integration_demo import stage_pipeline


def main():
    parser = argparse.ArgumentParser(description="Membrane contracts demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/contracts_demo")
    args = parser.parse_args()

    stage_pipeline(args.state_dir)
    rt = MembraneIntegrationRuntime(args.state_dir, require_impressions=True)
    rt.run()
    s = summary(rt.contracts)

    print("=== Membrane contracts demo ===")
    print(f"  contracts: {s['contract_count']}; violated: {s['violated_count']}")
    for c in s["contracts"]:
        print(f"  - {c['module']}: {c['status']}")
        for r in c["requirements"]:
            mark = "x" if r["satisfied"] else " "
            print(f"      [{mark}] {r['requirement']}"
                  + (f" -- {r['detail']}" if r["detail"] else ""))
    print("note: downstream modules should consume membrane-filtered sensory "
          "impressions, not raw events.")


if __name__ == "__main__":
    main()
