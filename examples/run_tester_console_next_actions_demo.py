#!/usr/bin/env python3
"""Tester console next-actions demo: no fixture, fixture pass, safety blocker.

    python examples/run_tester_console_next_actions_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_console_next_actions

Shows how the recommended next action changes across three synthetic scenarios: an
empty state (run the fixture demo), a clean fixture run (prepare live testing), and a
safety blocker (fix the blocker / stop). Next actions are recommendations only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_console import TesterConsoleRuntime
from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def _top_action(base, name, *, fixture=False, blocker=False):
    live = os.path.join(base, name, "live")
    tester = os.path.join(base, name, "tester")
    if fixture:
        TesterFixtureDemoRuntime(state_dir=tester,
                                 profile="fixture_tester_v0").run()
    if blocker:
        path = os.path.join(live, "membrane", "integration",
                            "MEMBRANE_INTEGRATION_REPORT.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump({"sections": {"status": {"critical_bypass_count": 1}}},
                  open(path, "w"))
    rt = TesterConsoleRuntime(state_dir=live, tester_state_dir=tester,
                              console_dir=os.path.join(base, name, "console"),
                              html=False)
    rt.run()
    return rt.next_actions[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_console_next_actions")
    args = ap.parse_args()
    base = args.tester_state_dir

    print("tester console next-actions demo")
    a = _top_action(base, "no_fixture")
    print(f"  no fixture       : [{a.priority}] {a.action}")
    a = _top_action(base, "fixture_pass", fixture=True)
    print(f"  fixture pass     : [{a.priority}] {a.action}")
    a = _top_action(base, "safety_blocker", fixture=True, blocker=True)
    print(f"  safety blocker   : [{a.priority}] {a.action}")
    print("note: next actions are recommendations only; the console never "
          "executes them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
