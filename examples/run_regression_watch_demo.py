#!/usr/bin/env python3
"""Regression watch demo: safety / test / ClaimGuard regression -> rollback.

    python examples/run_regression_watch_demo.py --state-dir .solaris_ai_nn_post_merge/test_regression_watch

Runs the regression watch and rollback watch over a candidate baseline that
regressed on safety and tests. A critical regression blocks baseline validation
and drives a rollback recommendation. Rollback is a recommendation only; it is
never executed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_merge_assimilation import (
    BaselineComparison,
    RegressionWatch,
    RollbackWatch,
)


def main():
    parser = argparse.ArgumentParser(description="Regression watch demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_post_merge/test_regression_watch")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    comparison = BaselineComparison().compare(
        parent_metrics={"safety_regression_status": False,
                        "test_pass_fail_status": "pass",
                        "claimguard_status": "pass"},
        candidate_metrics={"safety_regression_status": True,   # regression
                          "test_pass_fail_status": "fail",      # regression
                          "claimguard_status": "fail"})         # regression
    intake = {"critical_safety_regression_count": 1,
              "forbidden_file_change_count": 0, "test_failure_count": 2}
    regression = RegressionWatch().watch(comparison=comparison, intake=intake
                                         ).to_dict()
    rollback = RollbackWatch().build(
        regression=regression, intake=intake,
        validation={"artifacts": [
            {"artifact_type": "full_test_run", "present": True,
             "passed": False}]}).to_dict()

    print("=== Regression watch demo ===")
    print(f"regressions           : {regression['baseline_regression_count']} "
          f"(critical {regression['critical_regression_count']}, major "
          f"{regression['major_regression_count']})")
    for item in regression["items"]:
        print(f"  [{item['severity']}] {item['category']}: {item['detail']}")
    print(f"blocks validation     : {regression['blocks_validation']}")
    print(f"rollback              : {rollback['recommendation']} "
          f"({rollback['rollback_watch_trigger_count']} trigger(s))")
    print(f"rollback executed     : {rollback['executed']}")
    print("note                  : a critical regression blocks baseline "
          "validation; rollback is a recommendation only and is never "
          "executed; failed artifacts are preserved.")


if __name__ == "__main__":
    main()
