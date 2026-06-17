"""Safety freeze + packaging/console/feedback integration."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import run_freeze  # noqa: E402


def test_packaging_sees_safety_freeze_status(tmp_path):
    run_freeze(tmp_path)
    from solaris_ai_nn.tester_packaging import TesterPackagingRuntime
    pk = TesterPackagingRuntime(tester_state_dir=str(tmp_path))
    pk.run()
    sf = pk.packaging_status()["safety_freeze"]
    assert sf["safety_freeze_available"] is True
    assert "readiness" in sf


def test_console_shows_release_blockers(tmp_path):
    # Seed a forbidden-claim report so the freeze records an open blocker.
    os.makedirs(os.path.join(str(tmp_path), "reports"), exist_ok=True)
    with open(os.path.join(str(tmp_path), "reports", "BAD.md"), "w") as fh:
        fh.write("Solaris is conscious and has agency.")
    run_freeze(tmp_path)
    from solaris_ai_nn.tester_console import (
        ArtifactKind, SummaryCardKind, TesterConsoleRuntime)
    rt = TesterConsoleRuntime(
        state_dir=os.path.join(str(tmp_path), "live"),
        tester_state_dir=str(tmp_path),
        console_dir=os.path.join(str(tmp_path), "console"), html=False)
    rt.run()
    assert rt.discovery.has(ArtifactKind.TESTER_SAFETY_FREEZE_MANIFEST)
    sf_card = next(c for c in rt.cards
                   if c.kind == SummaryCardKind.SAFETY_FREEZE)
    assert sf_card is not None
    checks = {f.check for f in rt.safety_panel.findings}
    assert any("safety_freeze" in c for c in checks)


def test_feedback_blockers_included(tmp_path):
    # Ingest a release-blocker safety concern, then run the freeze; the evidence
    # picks up the feedback ledger counts.
    from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime
    samples = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "examples", "tester_feedback", "sample_release_blocker_feedback.json")
    TesterFeedbackRuntime(tester_state_dir=str(tmp_path),
                          ingest_path=samples).run()
    rt = run_freeze(tmp_path)
    assert "feedback_release_blocker_count" in rt.evidence
    assert rt.evidence.get("feedback_safety_concern_count", 0) >= 1
