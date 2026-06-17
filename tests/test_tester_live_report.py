"""Tester live report: generated, no-control disclaimers present, no unsupported claims."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime


def _report(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    return open(rt.reports["markdown"]).read(), rt


def test_report_generated(tmp_path):
    text, rt = _report(tmp_path)
    assert "# Tester Live-Read-Only Report" in text
    assert rt.reports["markdown"].endswith(".md")


def test_no_control_disclaimers_present(tmp_path):
    text, _ = _report(tmp_path)
    low = text.lower()
    assert "live-read-only testing" in low
    assert "external feeders are manual" in low
    assert "did not start/stop/control feeders" in low or \
        "start/stop/schedule/control" in low
    assert "no consciousness/life/agency claim is made" in low


def test_no_unsupported_claims(tmp_path):
    text, _ = _report(tmp_path)
    assert ClaimGuard().scan_text(text).safe


def test_external_feeder_policy_in_report(tmp_path):
    text, _ = _report(tmp_path)
    assert "External feeder policy" in text
    assert "Solaris starts feeders: False" in text
