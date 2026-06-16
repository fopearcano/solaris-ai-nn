#!/usr/bin/env python3
"""Next-cycle roadmap demo: next soak/replication + architecture input pack.

    python examples/run_next_cycle_roadmap_demo.py --state-dir .solaris_ai_nn_research_baseline/test_roadmap

Builds the next-cycle roadmap for a validated baseline (recommends mini soak,
replication, falsification, and architecture evolution) and for a blocked baseline
(requires evidence collection / safety improvement; soak is blocked). The roadmap
is planning only; it runs no task.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_baseline import build_roadmap_reset


def main():
    parser = argparse.ArgumentParser(description="Next-cycle roadmap demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research_baseline/test_roadmap")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    validated = build_roadmap_reset(
        validated=True, blocked=False,
        limitations={"limitations": [{"category": "fixture_overfit_risk"}]},
        validation={"validation_missing_count": 0}).to_dict()
    blocked = build_roadmap_reset(
        validated=False, blocked=True,
        limitations={"limitations": []},
        validation={"validation_missing_count": 2}).to_dict()

    print("=== Next-cycle roadmap demo ===")
    print(f"validated baseline    : {validated['roadmap_item_count']} item(s) "
          f"(required {validated['required_count']}, recommended "
          f"{validated['recommended_count']}, optional "
          f"{validated['optional_count']})")
    for item in validated["items"]:
        print(f"  [{item['priority']:11s}] {item['item_type']}")
    print(f"blocked baseline      : {blocked['roadmap_item_count']} item(s) "
          f"(required {blocked['required_count']}, blocked "
          f"{blocked['blocked_count']})")
    for item in blocked["items"]:
        print(f"  [{item['priority']:11s}] {item['item_type']}")
    print(f"executes tasks        : {validated['executes_tasks']}")
    print("note                  : the architecture-evolution input pack is the "
          "validated baseline's roadmap + capability map + limitations + "
          "anchors. The roadmap is planning only; it runs no task, creates no "
          "branch, and calls no external tool.")


if __name__ == "__main__":
    main()
