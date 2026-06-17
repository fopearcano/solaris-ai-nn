"""Feedback runtime: bounded, forms, ingest, reports, no behavior modification."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import sample_path  # noqa: E402


def test_bounded_runtime(tmp_path):
    rt = TesterFeedbackRuntime(tester_state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_forms_generated(tmp_path):
    rt = TesterFeedbackRuntime(tester_state_dir=str(tmp_path))
    rt.run()
    forms = os.path.join(rt.feedback_dir, "forms")
    assert os.path.isfile(os.path.join(forms, "TESTER_FEEDBACK_FORM.md"))
    assert os.path.isfile(os.path.join(forms, "BUG_REPORT_FORM.md"))


def test_sample_feedback_ingested(tmp_path):
    rt = TesterFeedbackRuntime(
        tester_state_dir=str(tmp_path),
        ingest_path=sample_path("sample_bug_report.json"))
    result = rt.run()
    assert result["entry_count"] == 1
    assert result["bug_report_count"] == 1


def test_reports_generated(tmp_path):
    rt = TesterFeedbackRuntime(
        tester_state_dir=str(tmp_path),
        ingest_path=sample_path("sample_safety_concern.json"))
    rt.run()
    reports = os.path.join(rt.feedback_dir, "reports")
    assert os.path.isfile(os.path.join(reports, "TESTER_FEEDBACK_REPORT.md"))


def test_no_behavior_modification(tmp_path):
    rt = TesterFeedbackRuntime(tester_state_dir=str(tmp_path))
    rt.run()
    st = rt.feedback_status()
    assert st["trains_on_feedback"] is False
    assert st["creates_github_issue"] is False
    assert st["uploads"] is False
    assert st["local_only"] is True


def test_doctor(tmp_path):
    rt = TesterFeedbackRuntime(tester_state_dir=str(tmp_path))
    doc = rt.run_doctor()
    assert doc["local_only"] is True
    assert doc["trains"] is False
