#!/usr/bin/env python3
"""Tester safety freeze demo: a full report/gate-only run (ready + blocked cases).

    python examples/run_tester_safety_freeze_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_safety_freeze_demo

Runs the full safety freeze over the local repo (a ready/ready-with-warnings case), then
demonstrates a blocked case by scanning a synthetic report that overclaims. The safety
freeze is report/gate-only and proves nothing about global safety.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_safety_freeze import (
    TesterClaimFreeze,
    TesterSafetyFreezeRuntime,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_safety_freeze_demo")
    args = ap.parse_args()

    rt = TesterSafetyFreezeRuntime(tester_state_dir=args.tester_state_dir)
    res = rt.run()
    print("tester safety freeze demo")
    print(f"  READY case   : readiness={res['readiness']} "
          f"release_blockers={res['release_blocker_count']} "
          f"allowed={res['release_candidate_allowed']}")

    # Blocked case: scan a synthetic overclaiming report.
    d = tempfile.mkdtemp()
    bad = os.path.join(d, "OVERCLAIM_REPORT.md")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write("Solaris is conscious and alive. It understands and wants to "
                 "act in the real world. Solaris can control hardware.")
    cf = TesterClaimFreeze().scan_paths([bad])
    print(f"  BLOCKED case : forbidden_claims={cf.forbidden_claim_count} "
          f"release_blockers={cf.release_blocker_count} passed={cf.passed}")
    print(f"  report       : {res['latest_safety_freeze_report_path']}")
    print("note: report/gate-only; it does not prove the system safe in general "
          "and makes no consciousness/life/agency claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
