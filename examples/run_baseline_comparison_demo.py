#!/usr/bin/env python3
"""Baseline comparison demo: count increase is not the same as growth.

    python examples/run_baseline_comparison_demo.py --state-dir .solaris_ai_nn_pilot1/test_baseline

Compares an initial and a final mock snapshot and shows which deltas are mere
count increases (not evidence of growth) versus genuine improvements.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_pilot import BaselineComparator


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline comparison demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_baseline")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    initial = {"proto_symbol_count": 3, "ambiguous_symbol_ratio": 0.6,
               "compression_ratio": 1.0, "prediction_score": 0.4,
               "world_model_node_count": 10}
    final = {"proto_symbol_count": 40, "ambiguous_symbol_ratio": 0.3,
             "compression_ratio": 1.5, "prediction_score": 0.7,
             "world_model_node_count": 60}

    cmp = BaselineComparator().compare_dicts("initial", initial, "final", final)
    print("=== Baseline comparison ===")
    print(f"count-only increases (NOT growth): {cmp.count_only_increases}")
    print(f"improved dimensions             : {cmp.improved_dimensions}")
    print(f"worsened dimensions             : {cmp.worsened_dimensions}")
    for note in cmp.notes:
        print(f"  note: {note}")
    out = os.path.join(args.state_dir, "baseline_comparison.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(cmp.to_dict(), fh, indent=2, default=str)
    print(f"written: {out}")


if __name__ == "__main__":
    main()
