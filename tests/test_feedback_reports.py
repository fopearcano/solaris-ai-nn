"""Feedback reports: all generated, release blocker + safety summary, ClaimGuard."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import ingest, sample_path  # noqa: E402


def _reports(tmp_path):
    tester = str(tmp_path / "t")
    ingest(tester, sample_path("sample_bug_report.json"))
    ingest(tester, sample_path("sample_release_blocker_feedback.json"))
    return os.path.join(tester, "feedback", "reports")


def test_all_reports_generated(tmp_path):
    reports = _reports(tmp_path)
    for name in ("TESTER_FEEDBACK_REPORT.md", "BUG_REPORT_SUMMARY.md",
                 "SAFETY_CONCERN_SUMMARY.md", "CONFUSION_REPORT_SUMMARY.md",
                 "SUGGESTION_REPORT_SUMMARY.md", "RELEASE_BLOCKER_REPORT.md",
                 "FEEDBACK_PRIVACY_REPORT.md", "FEEDBACK_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(reports, name)), name


def test_release_blocker_report_lists_blocker(tmp_path):
    reports = _reports(tmp_path)
    text = open(os.path.join(reports, "RELEASE_BLOCKER_REPORT.md")).read()
    assert "STOP TESTING" in text


def test_safety_concern_summary_generated(tmp_path):
    reports = _reports(tmp_path)
    text = open(os.path.join(reports, "SAFETY_CONCERN_SUMMARY.md")).read()
    assert "Safety Concern Summary" in text


def test_reports_claimguard_safe(tmp_path):
    reports = _reports(tmp_path)
    for name in os.listdir(reports):
        if name.endswith(".md"):
            text = open(os.path.join(reports, name)).read()
            assert ClaimGuard().scan_text(text).safe, name
