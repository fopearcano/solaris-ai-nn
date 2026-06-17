"""RC runbook: generated, fixture-first, governance warning, stop conditions."""

from __future__ import annotations

from solaris_ai_nn.tester_release_candidate import TesterRunbookBuilder


def test_runbook_generated(tmp_path):
    path = TesterRunbookBuilder().write(str(tmp_path))
    text = open(path, encoding="utf-8").read()
    assert "Tester Runbook" in text
    assert "pip install -e ." in text


def test_fixture_first_sequence():
    text = TesterRunbookBuilder().build_text().lower()
    assert text.index("fixture") < text.index("live-read")


def test_live_readonly_governance_warning():
    text = TesterRunbookBuilder().build_text().lower()
    assert "governance" in text
    assert "governance-gated" in text


def test_stop_conditions_present():
    text = TesterRunbookBuilder().build_text().lower()
    assert "stop conditions" in text
    assert "raw-event bypass" in text


def test_no_publish_or_feeder_start_commands():
    text = TesterRunbookBuilder().build_text().lower()
    assert "upload" not in text
    assert "publish" not in text
    assert "start feeders from solaris" not in text
