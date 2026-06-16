#!/usr/bin/env python3
"""Baseline comparison demo: improved, regressed, inconclusive, safety dominance.

    python examples/run_post_merge_baseline_comparison_demo.py --state-dir .solaris_ai_nn_post_merge/test_comparison

Compares a candidate baseline against its parent. The first comparison shows an
improved dimension and a regressed one. The second adds a safety regression: it
dominates the positive metrics, so the overall verdict is regressed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_merge_assimilation import BaselineComparison


def main():
    parser = argparse.ArgumentParser(
        description="Post-merge baseline comparison demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_post_merge/test_comparison")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    parent = {"sensorium_metrics": 0.5, "cognition_metrics": 0.4,
              "module_coverage": 0.8, "safety_regression_status": False,
              "test_pass_fail_status": "pass"}
    improved = BaselineComparison().compare(
        parent_metrics=parent,
        candidate_metrics={"sensorium_metrics": 0.65,    # improved
                           "cognition_metrics": 0.4,     # unchanged
                           "module_coverage": 0.75,      # regressed
                           "safety_regression_status": False,
                           "test_pass_fail_status": "pass"})

    safety = BaselineComparison().compare(
        parent_metrics=parent,
        candidate_metrics={"sensorium_metrics": 0.9,     # big improvement
                           "cognition_metrics": 0.8,     # big improvement
                           "safety_regression_status": True,  # regression!
                           "test_pass_fail_status": "pass"})

    print("=== Post-merge baseline comparison demo ===")
    print(f"case 1 overall        : {improved['overall']} "
          f"(improved {improved['improved_count']}, regressed "
          f"{improved['regressed_count']})")
    for r in improved["results"]:
        if r["status"] in ("improved", "regressed"):
            print(f"  {r['dimension']}: {r['status']} "
                  f"({r['parent_value']} -> {r['candidate_value']})")
    print(f"case 2 overall        : {safety['overall']} "
          f"(safety_regressed={safety['safety_regressed']})")
    print("  -> a safety regression dominates even large positive metrics")
    print(f"empty green dashboard : {improved['empty_green_dashboard']}")
    print("note                  : improvement requires evidence; a regression "
          "stays visible amid improvements; a safety regression dominates.")


if __name__ == "__main__":
    main()
