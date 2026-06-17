"""RC reports: all reports generated, readiness/safety report, ClaimGuard if available."""

from __future__ import annotations

import os

from _tester_rc_helpers import run_rc


def test_all_reports_generated(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    reports = os.path.join(rt.rc_dir, "reports")
    for name in ("TESTER_RC_REPORT.md", "TESTER_RC_REPORT.json",
                 "TESTER_RC_READINESS_REPORT.md",
                 "TESTER_RC_READINESS_REPORT.json",
                 "TESTER_RC_ARTIFACT_COLLECTION_REPORT.md",
                 "TESTER_RC_BUNDLE_REPORT.md", "TESTER_RC_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(reports, name)), name


def test_report_states_local_assembly(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    text = open(os.path.join(rt.rc_dir, "reports", "TESTER_RC_REPORT.md"),
                encoding="utf-8").read().lower()
    assert "local tester release-candidate assembly" in text
    assert "no public release was created" in text
    assert "no package was uploaded" in text


def test_safety_report_lists_hard_rules(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    text = open(os.path.join(rt.rc_dir, "reports", "TESTER_RC_SAFETY_REPORT.md"),
                encoding="utf-8").read().lower()
    assert "hard rules" in text
    assert "no publication/upload" in text


def test_claimguard_safe_flag(tmp_path):
    import json
    rt = run_rc(str(tmp_path / "rc"))
    data = json.load(open(os.path.join(rt.rc_dir, "reports",
                                       "TESTER_RC_REPORT.json")))
    assert data["claim_guard_safe"] in (True, False)
