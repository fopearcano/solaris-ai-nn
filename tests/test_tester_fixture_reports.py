"""Tester fixture reports: all reports generated, repro/regression, ClaimGuard safe."""

from __future__ import annotations

import os

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def _run(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    return os.path.join(str(tmp_path), "reports")


def test_all_reports_generated(tmp_path):
    reports = _run(tmp_path)
    for name in ("TESTER_FIXTURE_SPINE_REPORT.md", "GOLDEN_RUN_REPORT.md",
                 "REPRODUCIBILITY_REPORT.md", "REGRESSION_REPORT.md",
                 "TESTER_ARTIFACT_BUNDLE_REPORT.md",
                 "TESTER_FIXTURE_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(reports, name)), name


def test_reproducibility_report_generated(tmp_path):
    reports = _run(tmp_path)
    text = open(os.path.join(reports, "REPRODUCIBILITY_REPORT.md")).read()
    assert "Reproducibility Report" in text
    assert "status" in text.lower()


def test_regression_report_generated(tmp_path):
    reports = _run(tmp_path)
    text = open(os.path.join(reports, "REGRESSION_REPORT.md")).read()
    assert "Regression Report" in text


def test_all_reports_claimguard_safe(tmp_path):
    reports = _run(tmp_path)
    for name in os.listdir(reports):
        if name.endswith(".md"):
            text = open(os.path.join(reports, name)).read()
            assert ClaimGuard().scan_text(text).safe, name
