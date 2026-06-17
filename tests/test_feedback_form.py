"""Feedback form: generated, required fields, non-training ack, privacy warning."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import FeedbackCategory, TesterFeedbackForm


def test_form_generated():
    form = TesterFeedbackForm.build()
    d = form.to_dict()
    assert d["form_id"]
    assert len(d["categories"]) >= 20
    assert FeedbackCategory.SAFETY_CONCERN in d["categories"]
    assert FeedbackCategory.MEMBRANE_CONFUSION in d["categories"]


def test_required_fields_present():
    form = TesterFeedbackForm.build()
    req = form.required_keys()
    assert "category" in req
    assert "severity" in req
    assert "expected_behavior" in req
    assert "actual_behavior" in req


def test_non_training_acknowledgement_required():
    form = TesterFeedbackForm.build()
    assert "non_training_acknowledgement" in form.required_keys()
    assert "not training" in form.to_dict()["non_training_notice"].lower()


def test_privacy_warning_present():
    d = TesterFeedbackForm.build().to_dict()
    assert "secret" in d["privacy_notice"].lower()
    assert "do not include" in d["privacy_notice"].lower()


def test_markdown_states_not_training():
    md = TesterFeedbackForm.build().to_markdown().lower()
    assert "not training" in md
    assert "fixture-specific" in md
    assert "live-read-only" in md
