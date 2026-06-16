#!/usr/bin/env python3
"""Alpha cycle status demo: initialized, demo-completed-with-warnings, next action.

    python examples/run_alpha_cycle_status_demo.py --state-dir .solaris_ai_nn_alpha/test_cycle_status

Shows the descriptive alpha cycle status in three situations: just initialized (no
demo yet), demo completed with warnings (skipped optional modules), and a blocked
case. Cycle status is descriptive only -- it recommends a next action and never
executes it.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.alpha_system import determine_cycle_status


def _show(label, status):
    d = status.to_dict()
    print(f"  {label}")
    print(f"    stage       : {d['stage']}")
    print(f"    next action : {d['next_action']}")
    print(f"    blockers    : {d['blocker_count']}; warnings: "
          f"{d['warning_count']}")
    print(f"    executes    : {d['executes_next_action']}")


def main():
    parser = argparse.ArgumentParser(description="Alpha cycle status demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_alpha/test_cycle_status")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    print("=== Alpha cycle status demo ===")
    _show("initialized (no demo yet):", determine_cycle_status(
        initialized=True, doctor_blocked=False, demo_completed=False,
        warnings=0))
    print()
    _show("demo completed with warnings:", determine_cycle_status(
        initialized=True, doctor_blocked=False, demo_completed=True,
        warnings=3))
    print()
    _show("blocked:", determine_cycle_status(
        initialized=True, doctor_blocked=True, demo_completed=False,
        warnings=0, blockers=["module_registry_built"]))
    print("\nnote: alpha cycle status is descriptive only; it recommends a next "
          "action and never executes it. Blockers are explicit.")


if __name__ == "__main__":
    main()
