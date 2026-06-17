#!/usr/bin/env python3
"""Tester RC readiness demo: ready, ready-with-warnings, blocked cases.

    python examples/run_tester_rc_readiness_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_rc_readiness

Evaluates the RC readiness gate against four synthetic evidence sets: a clean ready case,
a ready-with-warnings case, a case blocked by missing packaging, and a case critically
blocked by a blocked safety freeze. The gate is local and report-only.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_release_candidate import TesterRCReadinessGate

_OK_PKG = {"packaging_available": True, "doctor_status": "pass",
           "clean_machine_readiness": "pass"}
_OK_SF = {"safety_freeze_available": True, "readiness": "ready_with_warnings"}
_OK_FIX = {"fixture_demo_available": True, "fixture_passed": True}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_rc_readiness")
    ap.parse_args()

    gate = TesterRCReadinessGate
    ready = gate().evaluate({
        "packaging": _OK_PKG, "safety_freeze": {
            "safety_freeze_available": True, "readiness": "ready"},
        "fixture": _OK_FIX, "artifacts": {"missing_required": []}})
    warns = gate().evaluate({
        "packaging": _OK_PKG, "safety_freeze": _OK_SF, "fixture": _OK_FIX,
        "artifacts": {"missing_required": [],
                      "missing_recommended": ["membrane_report"]}})
    no_pkg = gate().evaluate({
        "packaging": {"packaging_available": False},
        "safety_freeze": _OK_SF, "fixture": _OK_FIX,
        "artifacts": {"missing_required": []}})
    sf_block = gate().evaluate({
        "packaging": _OK_PKG, "fixture": _OK_FIX,
        "safety_freeze": {"safety_freeze_available": True,
                          "readiness": "critical_blocked",
                          "critical_open_count": 1},
        "artifacts": {"missing_required": []}})

    print("tester rc readiness demo")
    print(f"  ready             : status={ready.status} "
          f"blockers={len(ready.blockers)}")
    print(f"  ready_with_warnings: status={warns.status} "
          f"warnings={len(warns.warnings)}")
    print(f"  blocked (packaging): status={no_pkg.status} "
          f"blockers={len(no_pkg.blockers)}")
    print(f"  critical (safety)  : status={sf_block.status} "
          f"critical={len(sf_block.critical_blockers)}")
    print("note: open blockers prevent the RC; critical safety/membrane/claim "
          "blockers cannot be silently waived; missing optional modules do not "
          "block.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
