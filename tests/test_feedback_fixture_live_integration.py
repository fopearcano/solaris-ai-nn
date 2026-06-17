"""Feedback fixture/live integration: fixture + live fields, membrane category."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import FeedbackCategory, TesterFeedbackForm


def test_fixture_specific_fields_exist():
    cats = set(FeedbackCategory.ALL)
    assert FeedbackCategory.FIXTURE_DEMO_FAILURE in cats
    assert FeedbackCategory.FIXTURE_REPRODUCIBILITY_PROBLEM in cats
    assert FeedbackCategory.FIXTURE_REGRESSION_PROBLEM in cats
    md = TesterFeedbackForm.build().to_markdown().lower()
    assert "fixture command run" in md
    assert "golden manifest problem" in md


def test_live_specific_fields_exist():
    cats = set(FeedbackCategory.ALL)
    assert FeedbackCategory.GOVERNANCE_CONFUSION in cats
    assert FeedbackCategory.FEEDER_REGISTRY_CONFUSION in cats
    assert FeedbackCategory.LIVE_BIRTH_PROBLEM in cats
    md = TesterFeedbackForm.build().to_markdown().lower()
    assert "governance confusion" in md
    assert "membrane bypass concern" in md


def test_membrane_confusion_category_exists():
    cats = set(FeedbackCategory.ALL)
    assert FeedbackCategory.MEMBRANE_CONFUSION in cats
    assert FeedbackCategory.MEMBRANE_BYPASS_CONCERN in cats
    assert FeedbackCategory.QUARANTINE_CONFUSION in cats
