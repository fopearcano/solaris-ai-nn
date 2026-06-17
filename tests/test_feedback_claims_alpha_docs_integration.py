"""Feedback claims/alpha/docs: claim classified, alpha status, docs non-training."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_feedback import ReleaseBlockerClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import ingest, sample_path  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_unsupported_claim_feedback_classified():
    c = ReleaseBlockerClassifier().classify(
        {"category": "unsupported_claim_concern", "feedback_id": "f1"})
    assert c.is_release_blocker is True


def test_alpha_exposes_feedback_status(tmp_path):
    tester = str(tmp_path / "t")
    ingest(tester, sample_path("sample_bug_report.json"))
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    status = AlphaResearchOrchestrator().tester_feedback_status(
        tester_state_dir=tester)
    assert status["feedback_available"] is True
    assert status["trains_on_feedback"] is False
    assert status["feedback_entry_count"] >= 1


def test_alpha_absent_without_feedback(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    status = AlphaResearchOrchestrator().tester_feedback_status(
        tester_state_dir=str(tmp_path / "none"))
    assert status["feedback_available"] is False


def test_docs_include_non_training_explanation():
    for rel in ("README.md", os.path.join("docs", "ARCHITECTURE.md")):
        text = open(os.path.join(_ROOT, rel)).read().lower()
        assert "feedback" in text
        assert "not training" in text or "not the human feedback" in text
