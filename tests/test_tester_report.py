"""Tester report: generated, fixture-only disclaimer, safety boundaries, skips visible."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def _report_text(state_dir, profile="fixture_tester_v0"):
    rt = TesterFixtureDemoRuntime(state_dir=state_dir, profile=profile)
    rt.run()
    return open(rt.reports["markdown"]).read(), rt


def test_tester_report_generated(tmp_path):
    text, rt = _report_text(str(tmp_path))
    assert "# Tester Demo Report" in text
    assert rt.reports["markdown"].endswith(".md")


def test_fixture_only_disclaimer_present(tmp_path):
    text, _ = _report_text(str(tmp_path))
    assert "fixture-only tester demo" in text.lower()
    assert "no live data was required" in text.lower()


def test_safety_boundaries_included(tmp_path):
    text, _ = _report_text(str(tmp_path))
    low = text.lower()
    assert "no feeder was started" in low
    assert "no tester feedback was used as training" in low
    assert "no consciousness/life/agency claim is made" in low


def test_skipped_stages_visible(tmp_path):
    text, rt = _report_text(str(tmp_path), profile="fixture_membrane_only_v0")
    assert rt.skipped_stages
    low = text.lower()
    assert "skipped honestly" in low


def test_report_claimguard_safe(tmp_path):
    from solaris_ai_nn.governance.compliance import ClaimGuard
    text, _ = _report_text(str(tmp_path))
    assert ClaimGuard().scan_text(text).safe
