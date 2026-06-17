#!/usr/bin/env python3
"""Tester console status demo: pass, warnings, blockers, missing optional.

    python examples/run_tester_console_status_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_console_status

Builds the console status over three synthetic scenarios -- a clean fixture run (pass),
a fixture run plus disabled governance (warnings), and an empty state (missing required
stage blocker) -- showing how the status model distinguishes pass / warnings / blocked
and how optional missing layers are not failures.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_console import TesterConsoleRuntime
from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def _console(base, name, with_fixture=False, with_disabled_gov=False):
    live = os.path.join(base, name, "live")
    tester = os.path.join(base, name, "tester")
    if with_fixture:
        TesterFixtureDemoRuntime(state_dir=tester,
                                 profile="fixture_tester_v0").run()
    if with_disabled_gov:
        import json
        os.makedirs(os.path.join(live, "governance"), exist_ok=True)
        json.dump({"live_readonly_enabled": False, "operator_approved": False,
                   "allowed_sources": [], "forbidden_sources": []},
                  open(os.path.join(live, "governance",
                                    "LIVE_READONLY_GOVERNANCE.json"), "w"))
    rt = TesterConsoleRuntime(state_dir=live, tester_state_dir=tester,
                              console_dir=os.path.join(base, name, "console"),
                              html=False)
    rt.run()
    return rt.console_status(), rt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_console_status")
    args = ap.parse_args()
    base = args.tester_state_dir

    print("tester console status demo")
    st, _ = _console(base, "pass", with_fixture=True)
    print(f"  fixture pass      : health={st['overall_health']} "
          f"safety={st['safety_status']}")
    st, rt = _console(base, "warnings", with_fixture=True,
                      with_disabled_gov=True)
    print(f"  disabled gov      : health={st['overall_health']} "
          f"safety={st['safety_status']}")
    st, rt = _console(base, "blocked")
    missing = rt.dashboard.sections["missing_artifacts"]
    print(f"  empty state       : health={st['overall_health']} "
          f"missing_required={missing}")
    skipped = rt.dashboard.sections["skipped_optional_stages"]
    print(f"  optional skipped  : {skipped} (not a failure)")
    print("note: missing optional layers are not failures; safety blockers "
          "override cosmetic success.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
