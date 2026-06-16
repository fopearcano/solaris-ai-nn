#!/usr/bin/env python3
"""Capability map demo: validated, experimental, and missing capabilities.

    python examples/run_capability_map_demo.py --state-dir .solaris_ai_nn_research_baseline/test_capability_map

Builds the baseline capability map: a validated capability (with evidence refs),
an experimental capability, a declared-validated capability *without* evidence
(downgraded to available), and the limitation refs each carries. "Capability"
means an implemented module with available evidence -- not intelligence.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_baseline import BaselineCapabilityMap


def main():
    parser = argparse.ArgumentParser(description="Capability map demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_research_baseline/test_capability_map")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    cap = BaselineCapabilityMap().build(evidence={
        "plural_sensorium": {"status": "validated",
                             "evidence_refs": ["replication:ok", "soak:ok"],
                             "limitations": ["fixture-weighted evidence"]},
        "semiogenesis": {"status": "experimental",
                         "evidence_refs": ["unit_tests"],
                         "limitations": ["no live grounding yet"]},
        # Declared validated but WITHOUT evidence refs -> downgraded to available.
        "developmental_soak": {"status": "validated", "evidence_refs": []},
    }).to_dict()

    print("=== Capability map demo ===")
    print(f"capabilities          : {cap['capability_count']} "
          f"(validated {cap['validated_capability_count']})")
    for area in ("plural_sensorium", "semiogenesis", "developmental_soak"):
        rec = cap["records"][area]
        print(f"  {area:20s} {rec['status']:12s} "
              f"refs={rec['evidence_refs']} limits={rec['limitations']}")
    missing = [a for a, r in cap["records"].items() if r["status"] == "missing"]
    print(f"missing capabilities  : {missing or 'none'}")
    print("note                  : capability means an implemented module with "
          "available evidence, not intelligence or understanding; a "
          "validated claim without evidence refs is downgraded to available.")


if __name__ == "__main__":
    main()
