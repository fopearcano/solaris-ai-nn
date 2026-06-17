"""Feedback ledger: append-only, index generated, old entries preserved, redaction."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_feedback import (
    FeedbackLedgerEntry,
    TesterFeedbackLedger,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import ingest, sample_path, write_feedback  # noqa: E402


def test_ledger_append_only(tmp_path):
    ledger = TesterFeedbackLedger(ledger_dir=str(tmp_path))
    ledger.append(FeedbackLedgerEntry(feedback_id="f1", feedback_type="bug"))
    ledger.append(FeedbackLedgerEntry(feedback_id="f2", feedback_type="bug"))
    assert len(ledger.load().entries) == 2
    # Appending again does not delete prior entries.
    ledger.append(FeedbackLedgerEntry(feedback_id="f3"))
    assert len(ledger.load().entries) == 3


def test_index_generated(tmp_path):
    ledger = TesterFeedbackLedger(ledger_dir=str(tmp_path))
    ledger.append(FeedbackLedgerEntry(feedback_id="f1",
                                      feedback_type="safety_concern",
                                      release_blocker_status="release_blocker"))
    ledger.write_index()
    assert os.path.isfile(ledger.index_path)
    assert os.path.isfile(ledger.json_path)
    index = ledger.load()
    assert index.release_blocker_count == 1
    assert index.safety_concern_count == 1


def test_old_entries_preserved(tmp_path):
    tester = str(tmp_path / "t")
    ingest(tester, sample_path("sample_bug_report.json"))
    ingest(tester, sample_path("sample_suggestion.json"))
    ledger = TesterFeedbackLedger(
        ledger_dir=os.path.join(tester, "feedback", "ledger"))
    assert len(ledger.load().entries) == 2


def test_redaction_recorded(tmp_path):
    tester = str(tmp_path / "t")
    path = write_feedback(tmp_path, "secret.json", {
        "feedback_type": "bug_report", "feedback_id": "leak",
        "actual_behavior": "the password is hunter2 and api_key=ABC",
        "non_training_acknowledgement": True})
    rt = ingest(tester, path)
    assert rt.redactions
    ledger = TesterFeedbackLedger(
        ledger_dir=os.path.join(tester, "feedback", "ledger"))
    entry = ledger.load().entries[0]
    assert entry.privacy_redaction_status == "redacted"
