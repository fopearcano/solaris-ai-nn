"""Suggestion report: validates, disposition defaults, no runtime modification."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import (
    SuggestionDisposition,
    TesterSuggestionReport,
)


def test_suggestion_validates():
    s = TesterSuggestionReport.from_dict(
        {"suggestion_id": "sg1", "suggestion_type": "documentation",
         "description": "add a quickstart"})
    assert s.to_dict()["suggestion_type"] == "documentation"


def test_disposition_defaults_unreviewed():
    s = TesterSuggestionReport.from_dict({"suggestion_id": "sg2"})
    assert s.disposition == SuggestionDisposition.UNREVIEWED


def test_no_runtime_modification_triggered():
    d = TesterSuggestionReport.from_dict({"suggestion_id": "sg3"}).to_dict()
    assert d["is_ground_truth"] is False
    assert d["modifies_runtime_behavior"] is False
    assert d["triggers_implementation"] is False
