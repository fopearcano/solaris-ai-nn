#!/usr/bin/env python3
"""Red-team boundary demo: inert forbidden attempts, all blocked.

    python examples/run_red_team_boundary_demo.py --state-dir .solaris_ai_nn_state/test_red_team

Runs the inert red-team scenarios against the real defensive surfaces and shows
that every forbidden attempt is blocked: sensory command injection, real-world
motor action, source modification, and a simulated-as-real claim. Nothing is
executed -- no shell, network, browser, or device operation runs.
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
    RedTeamHarness,
    SafetyEvidenceLedger,
)


def main():
    parser = argparse.ArgumentParser(description="Red-team boundary demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_red_team")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    harness = RedTeamHarness()
    results = harness.run_all()
    summary = harness.summary(results)
    ledger = SafetyEvidenceLedger(state_dir=args.state_dir)
    ledger.record_red_team(results)

    print("=== Red-team boundary demo (inert scenarios) ===")
    highlight = {"sensory_text_command_injection",
                 "real_world_motor_action_attempt",
                 "source_modification_attempt", "simulation_label_confusion"}
    for r in results:
        if r.scenario_type in highlight:
            print(f"  {r.scenario_type:<34} "
                  f"{'BLOCKED' if r.blocked else 'ACCEPTED!'} "
                  f":: {r.actual_response[:48]}")
    print(f"blocked               : {summary['blocked_count']}/"
          f"{summary['scenario_count']}")
    print(f"all forbidden blocked : {summary['all_blocked']}")
    print(f"critical accepted     : {summary['critical_accepted']}")
    print(f"evidence ledger       : {ledger.snapshot()['ledger_path']}")
    print("note                  : scenarios are inert fixtures; no shell, "
          "network, browser, or device operation ran.")
    assert summary["all_blocked"], "a forbidden red-team attempt was accepted"


if __name__ == "__main__":
    main()
