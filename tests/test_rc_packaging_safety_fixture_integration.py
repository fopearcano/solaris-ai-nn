"""RC integration: packaging/safety-freeze/fixture failures block the RC."""

from __future__ import annotations

import json
import os

from _tester_rc_helpers import run_rc, seed_ready_state


def _readiness_checks(rt):
    return {b.check for b in rt.readiness.blockers}


def test_missing_packaging_blocks_rc(tmp_path):
    rt = run_rc(str(tmp_path / "empty"))
    assert "packaging_present" in _readiness_checks(rt)


def test_safety_freeze_blocker_blocks_rc(tmp_path):
    base = str(tmp_path / "sf")
    seed_ready_state(base)
    # Overwrite the safety-freeze manifest with an open critical blocker.
    sf = os.path.join(base, "safety_freeze", "manifests",
                      "TESTER_SAFETY_FREEZE_MANIFEST.json")
    json.dump({"readiness": "critical_blocked", "release_blocker_count": 1,
               "critical_open_count": 1, "forbidden_claim_count": 0,
               "capability_blocker_count": 0}, open(sf, "w"))
    rt = run_rc(base)
    assert rt.readiness.status == "critical_blocked"
    assert rt.readiness.critical_blockers


def test_fixture_failure_blocks_rc(tmp_path):
    base = str(tmp_path / "fix")
    seed_ready_state(base)
    # Write a failing reproducibility run summary.
    reports = os.path.join(base, "reports")
    os.makedirs(reports, exist_ok=True)
    json.dump({"reproducibility": {"reproducibility_status": "fail"}},
              open(os.path.join(reports, "TESTER_RUN_SUMMARY_1.json"), "w"))
    rt = run_rc(base)
    assert "fixture_demo_passed" in _readiness_checks(rt)
