"""First tester post-test review: template, confusion/overclaim, non-training."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import FirstTesterPostTestReview


def test_review_template_generated(tmp_path):
    path = FirstTesterPostTestReview().write(str(tmp_path))
    text = open(path, encoding="utf-8").read()
    assert "First Tester Post-Test Review Template" in text


def test_confusion_questions_present():
    text = FirstTesterPostTestReview().build_text().lower()
    assert "first confusing moment" in text
    assert "block a second tester" in text


def test_overclaim_question_present():
    text = FirstTesterPostTestReview().build_text().lower()
    assert "overclaim" in text


def test_feedback_non_training_statement_present():
    d = FirstTesterPostTestReview().to_dict()
    assert d["is_training"] is False
    assert d["is_ground_truth"] is False
    assert d["modifies_solaris"] is False
    text = FirstTesterPostTestReview().build_text().lower()
    assert "not training" in text
