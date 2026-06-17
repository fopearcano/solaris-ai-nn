"""Packaging reports: all generated, safety report, ClaimGuard-safe."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.governance.compliance import ClaimGuard

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_packaging_helpers import run_packaging  # noqa: E402


def test_all_reports_generated(tmp_path):
    rt = run_packaging(tmp_path)
    reports = os.path.join(rt.packaging_dir, "reports")
    for name in ("PACKAGING_REPORT.md", "PACKAGING_REPORT.json",
                 "DEPENDENCY_CHECK_REPORT.md", "ENVIRONMENT_DOCTOR_REPORT.md",
                 "COMMAND_REGISTRY_REPORT.md",
                 "CLEAN_MACHINE_READINESS_REPORT.md",
                 "PLATFORM_NOTES_REPORT.md", "PACKAGING_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(reports, name)), name


def test_safety_report_generated(tmp_path):
    rt = run_packaging(tmp_path)
    text = open(os.path.join(rt.packaging_dir, "reports",
                             "PACKAGING_SAFETY_REPORT.md")).read()
    assert "Packaging Safety Report" in text
    assert "no global package install" in text


def test_reports_claimguard_safe(tmp_path):
    rt = run_packaging(tmp_path)
    reports = os.path.join(rt.packaging_dir, "reports")
    for name in os.listdir(reports):
        if name.endswith(".md"):
            text = open(os.path.join(reports, name)).read()
            assert ClaimGuard().scan_text(text).safe, name
