"""Reviewer questions: hostile generated, linked to claims, no answers invented."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    ReviewerQuestionCategory,
    ReviewerQuestionGenerator,
)


def test_hostile_questions_generated():
    questions = ReviewerQuestionGenerator().generate()
    cats = {q.category for q in questions}
    assert ReviewerQuestionCategory.FALSIFICATION in cats
    assert ReviewerQuestionCategory.ALTERNATIVE_EXPLANATIONS in cats
    assert ReviewerQuestionCategory.FORBIDDEN_CLAIMS in cats
    text = " ".join(q.text for q in questions).lower()
    assert "passive" in text or "falsif" in text


def test_questions_link_to_claims_where_available():
    claims = [{"claim_id": "c1", "category": "sensorium_claim"},
              {"claim_id": "c2", "category": "replication_claim"}]
    questions = ReviewerQuestionGenerator().generate(claims=claims)
    by_cat = {q.category: q for q in questions}
    assert "c1" in by_cat[ReviewerQuestionCategory.SENSORIUM].claim_refs
    assert "c2" in by_cat[ReviewerQuestionCategory.REPLICATION].claim_refs


def test_no_answers_invented():
    questions = ReviewerQuestionGenerator().generate()
    for q in questions:
        d = q.to_dict()
        assert d["answer_required_now"] is False
        assert "answer" not in d  # questions carry no answer field


def test_summary_counts():
    questions = ReviewerQuestionGenerator().generate()
    summary = ReviewerQuestionGenerator.summary(questions)
    assert summary["reviewer_question_count"] == len(questions)
