"""Tester live reports: all reports generated, ClaimGuard-safe."""

from __future__ import annotations

import os

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime


def _run(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    return os.path.join(str(tmp_path / "tester"), "reports")


def test_all_reports_generated(tmp_path):
    reports = _run(tmp_path)
    for name in ("TESTER_LIVE_READONLY_SPINE_REPORT.md",
                 "TESTER_LIVE_DOCTOR_REPORT.md", "TESTER_LIVE_CHECKLIST.md",
                 "TESTER_SAFE_EVENT_PACK_REPORT.md",
                 "TESTER_FEEDER_TEMPLATE_REPORT.md",
                 "TESTER_LIVE_BUNDLE_REPORT.md",
                 "TESTER_LIVE_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(reports, name)), name


def test_reports_claimguard_safe(tmp_path):
    reports = _run(tmp_path)
    for name in os.listdir(reports):
        if name.endswith(".md"):
            text = open(os.path.join(reports, name)).read()
            assert ClaimGuard().scan_text(text).safe, name
