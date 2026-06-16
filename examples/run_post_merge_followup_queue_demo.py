#!/usr/bin/env python3
"""Post-merge follow-up queue demo: missing validation, soak/replication queue.

    python examples/run_post_merge_followup_queue_demo.py --state-dir .solaris_ai_nn_post_merge/test_followup

Builds the follow-up queue for two candidate baselines: one with missing
validation (queues reruns), and one validated baseline (queues mini soak,
falsification replay, and replication registration). The queue is local metadata;
it executes nothing.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_merge_assimilation import build_followup_queue


def main():
    parser = argparse.ArgumentParser(
        description="Post-merge follow-up queue demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_post_merge/test_followup")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    missing = build_followup_queue(
        validation={"missing_required": ["full_test_run",
                                         "safety_invariant_run"]},
        regression={"baseline_regression_count": 1},
        module_status={}, rollback={"recommendation": "request_revision"},
        baseline_validated=False).to_dict()

    validated = build_followup_queue(
        validation={"missing_required": []},
        regression={"baseline_regression_count": 0},
        module_status={}, rollback={"recommendation": "no_rollback_needed"},
        baseline_validated=True).to_dict()

    print("=== Post-merge follow-up queue demo ===")
    print(f"missing-validation queue : {missing['followup_item_count']} item(s)")
    for item in missing["items"]:
        print(f"  [{item['priority']}] {item['item_type']}")
    print(f"validated-baseline queue : {validated['followup_item_count']} item(s)")
    for item in validated["items"]:
        print(f"  [{item['priority']}] {item['item_type']}")
    print(f"executes tasks           : {validated['executes_tasks']}")
    print("note                     : the follow-up queue is local metadata; it "
          "executes no task, calls no external tool, and modifies no source.")


if __name__ == "__main__":
    main()
