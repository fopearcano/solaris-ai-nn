"""Console reports: report set generated, ClaimGuard-safe."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.governance.compliance import ClaimGuard

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console  # noqa: E402


def test_reports_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    for name in ("CONSOLE_REPORT.md", "CONSOLE_REPORT.json",
                 "CONSOLE_STATUS.json"):
        assert os.path.isfile(os.path.join(rt.console_dir, name)), name


def test_artifact_discovery_report_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    reports = os.path.join(rt.console_dir, "reports")
    assert os.path.isfile(os.path.join(reports,
                                       "CONSOLE_ARTIFACT_DISCOVERY.md"))


def test_next_action_report_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    reports = os.path.join(rt.console_dir, "reports")
    assert os.path.isfile(os.path.join(reports, "CONSOLE_NEXT_ACTIONS.md"))
    assert os.path.isfile(os.path.join(reports, "CONSOLE_SAFETY_PANEL.md"))


def test_reports_claimguard_safe(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    for root, _dirs, files in os.walk(rt.console_dir):
        for name in files:
            if name.endswith(".md"):
                text = open(os.path.join(root, name)).read()
                assert ClaimGuard().scan_text(text).safe, name
