"""Safety freeze reports: all generated, release blocker report, ClaimGuard-safe."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.governance.compliance import ClaimGuard

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import run_freeze  # noqa: E402


def test_all_reports_generated(tmp_path):
    rt = run_freeze(tmp_path)
    reports = os.path.join(str(tmp_path), "safety_freeze", "reports")
    for name in ("TESTER_SAFETY_FREEZE_REPORT.md",
                 "TESTER_SAFETY_FREEZE_REPORT.json",
                 "TESTER_CLAIM_FREEZE_REPORT.md",
                 "TESTER_CAPABILITY_FREEZE_REPORT.md",
                 "TESTER_ARTIFACT_SAFETY_SCAN.md", "TESTER_RED_TEAM_REPORT.md",
                 "TESTER_RELEASE_BLOCKERS.md", "TESTER_RELEASE_BLOCKERS.json"):
        assert os.path.isfile(os.path.join(reports, name)), name


def test_release_blocker_report_generated(tmp_path):
    rt = run_freeze(tmp_path)
    text = open(os.path.join(str(tmp_path), "safety_freeze", "reports",
                             "TESTER_RELEASE_BLOCKERS.md")).read()
    assert "Tester Release Blockers" in text


def test_reports_claimguard_safe(tmp_path):
    rt = run_freeze(tmp_path)
    reports = os.path.join(str(tmp_path), "safety_freeze", "reports")
    for name in os.listdir(reports):
        if name.endswith(".md"):
            text = open(os.path.join(reports, name)).read()
            assert ClaimGuard().scan_text(text).safe, name
