#!/usr/bin/env python3
"""Pilot-1 exit criteria demo: success, failure, and inconclusive cases.

    python examples/run_pilot1_exit_criteria_demo.py --state-dir .solaris_ai_nn_pilot1/test_exit_criteria

Evaluates three observation snapshots through the exit-criteria engine and
prints the decision for each. Reminder: pilot success means operational
completion and an analyzable trace -- never proof of consciousness.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot1 import PilotExitCriteria


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-1 exit criteria demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_exit_criteria")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    ec = PilotExitCriteria()
    success = ec.evaluate({
        "target_duration_reached": True, "uptime_ratio": 0.99,
        "checkpoint_failure": 0, "unresolved_critical_safety": 0,
        "report_count": 3, "structural_change_score": 0.2,
        "observability_complete": True})
    failure = ec.evaluate({"emergency_stop": True, "uptime_ratio": 0.5})
    inconclusive = ec.evaluate({
        "target_duration_reached": True, "uptime_ratio": 0.4,
        "report_count": 0, "structural_change_score": 0.0,
        "observability_complete": False})

    print("=== Pilot-1 exit criteria demo ===")
    print(f"success case      : {success.decision} "
          f"(success={success.success})")
    print(f"failure case      : {failure.decision} "
          f"(must_stop={failure.must_stop})")
    print(f"inconclusive case : {inconclusive.decision}")
    print(f"disclaimer        : {success.consciousness_disclaimer}")


if __name__ == "__main__":
    main()
