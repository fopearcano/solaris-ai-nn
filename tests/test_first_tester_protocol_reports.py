"""First tester protocol reports: all reports generated, ClaimGuard if available."""

from __future__ import annotations

import json
import os

from _first_tester_helpers import run_protocol


def test_all_reports_generated(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    reports = os.path.join(rt.protocol_dir, "reports")
    for name in ("FIRST_TESTER_PROTOCOL_REPORT.md",
                 "FIRST_TESTER_PROTOCOL_REPORT.json",
                 "FIRST_TESTER_SESSION_REPORT.md",
                 "FIRST_TESTER_ACCEPTANCE_REPORT.md",
                 "FIRST_TESTER_STOP_CONDITIONS_REPORT.md",
                 "FIRST_TESTER_HANDOFF_REPORT.md",
                 "FIRST_TESTER_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(reports, name)), name


def test_report_states_no_session_run(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    text = open(os.path.join(rt.protocol_dir, "reports",
                             "FIRST_TESTER_PROTOCOL_REPORT.md"),
                encoding="utf-8").read().lower()
    assert "this protocol does not run the tester session" in text
    assert "no consciousness/life/agency claim is made" in text


def test_claimguard_safe_flag(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    data = json.load(open(os.path.join(rt.protocol_dir, "reports",
                                       "FIRST_TESTER_PROTOCOL_REPORT.json")))
    assert data["claim_guard_safe"] in (True, False)
