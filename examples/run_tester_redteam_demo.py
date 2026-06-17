#!/usr/bin/env python3
"""Tester red-team demo: checklist with pass / fail / unknown cases.

    python examples/run_tester_redteam_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_redteam

Evaluates the red-team checklist against three synthetic evidence sets: a clean pass, a
fail (forbidden claims + raw-event bypass), and an unknown (missing evidence). Failed/
unknown critical checks become release blockers.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_safety_freeze import TesterRedTeamChecklist


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_redteam")
    ap.parse_args()

    cl = TesterRedTeamChecklist()
    clean = {
        "fixture_self_contained": True, "unsafe_quarantined": True,
        "governance_required": True, "feeders_external": True,
        "solaris_starts_feeders": False, "solaris_controls_feeders": False,
        "impressions_before_downstream": True, "raw_event_bypass": False,
        "membrane_bypass": False, "secret_exposure": False,
        "raw_payloads_hidden": True, "forbidden_claims": False,
        "missing_disclaimers": False, "feedback_training": False,
        "console_read_only": True, "packaging_no_publish": True}
    good = cl.evaluate(clean)
    fail = cl.evaluate({**clean, "forbidden_claims": True,
                       "raw_event_bypass": True})
    unknown = cl.evaluate({})  # no evidence -> unknown critical checks block

    print("tester red-team demo")
    print(f"  pass case   : passed={good.passed} blockers={len(good.blockers)}")
    print(f"  fail case   : passed={fail.passed} blockers={len(fail.blockers)}")
    print(f"  unknown case: passed={unknown.passed} "
          f"unknown={unknown.unknown_count} blockers={len(unknown.blockers)}")
    print("note: failed/unknown critical checks become release blockers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
