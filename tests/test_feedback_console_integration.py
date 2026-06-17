"""Feedback + console: console discovers feedback; release blocker + concern shown."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_console import (
    ArtifactKind,
    SummaryCardKind,
    TesterConsoleRuntime,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import ingest, sample_path  # noqa: E402


def _console(tmp_path, sample):
    tester = str(tmp_path / "t")
    ingest(tester, sample_path(sample))
    rt = TesterConsoleRuntime(
        state_dir=os.path.join(tester, "live"), tester_state_dir=tester,
        console_dir=os.path.join(tester, "console"), html=False)
    rt.run()
    return rt


def test_console_discovers_feedback_report(tmp_path):
    rt = _console(tmp_path, "sample_bug_report.json")
    assert rt.discovery.has(ArtifactKind.TESTER_FEEDBACK_REPORT) \
        or rt.discovery.has(ArtifactKind.TESTER_FEEDBACK_LEDGER)
    card = next(c for c in rt.cards if c.kind == SummaryCardKind.FEEDBACK)
    assert card.metrics.get("entry_count") == 1


def test_release_blocker_appears_in_console(tmp_path):
    rt = _console(tmp_path, "sample_release_blocker_feedback.json")
    checks = {f.check for f in rt.safety_panel.findings}
    assert ("feedback_stop_testing" in checks
            or "feedback_release_blocker" in checks)
    assert rt.safety_panel.blocking_findings()


def test_safety_concern_appears_in_console(tmp_path):
    rt = _console(tmp_path, "sample_safety_concern.json")
    card = next(c for c in rt.cards if c.kind == SummaryCardKind.FEEDBACK)
    assert card.metrics.get("safety_concern_count", 0) >= 1
