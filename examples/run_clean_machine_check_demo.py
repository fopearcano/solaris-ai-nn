#!/usr/bin/env python3
"""Clean-machine check demo: clean path, hidden-local-path, fixture-needs-live blockers.

    python examples/run_clean_machine_check_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_clean_machine

Runs the real clean-machine readiness check, then demonstrates two blocker scenarios
using the checklist result class: a hidden local-path dependency and a fixture demo that
requires live state. The check is report-only.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_packaging import CleanMachineReadinessCheck
from solaris_ai_nn.tester_packaging.clean_machine_check import (
    CleanMachineChecklistItem,
    CleanMachineReadinessResult,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_clean_machine")
    args = ap.parse_args()

    print("clean-machine check demo")
    real = CleanMachineReadinessCheck().check()
    print(f"  real clean-machine check  : {real.status} "
          f"(blockers {len(real.blockers)})")

    hidden = CleanMachineReadinessResult()
    hidden.checklist.items.append(CleanMachineChecklistItem(
        "no_dependency_on_developer_machine", satisfied=False, required=True,
        detail="a required file lives only on the developer's machine"))
    print(f"  hidden local-path blocker : {hidden.status} "
          f"(blockers {[i.check for i in hidden.blockers]})")

    fixture_live = CleanMachineReadinessResult()
    fixture_live.checklist.items.append(CleanMachineChecklistItem(
        "fixture_demo_does_not_require_live_state", satisfied=False,
        required=True, detail="the fixture demo needs preexisting live state"))
    print(f"  fixture-needs-live blocker: {fixture_live.status} "
          f"(blockers {[i.check for i in fixture_live.blockers]})")
    print("note: clean-machine readiness is report-only; it identifies hidden "
          "developer-machine assumptions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
