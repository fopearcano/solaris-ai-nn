"""Objection classifier: classified, critical blocks, invalid needs refs."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    ObjectionCategory,
    ObjectionSeverity,
    ObjectionValidityStatus,
    ReviewerObjectionClassifier,
)


def test_objections_classified():
    classifier = ReviewerObjectionClassifier()
    cs = classifier.classify([
        {"objection_id": "o1", "text": "There is no evidence for this."},
        {"objection_id": "o2", "text": "Probably fixture overfit."},
        {"objection_id": "o3", "text": "Could be a passive parser artifact."}])
    cats = {c.category for c in cs}
    assert ObjectionCategory.MISSING_EVIDENCE in cats
    assert ObjectionCategory.FIXTURE_OVERFIT in cats
    assert ObjectionCategory.PASSIVE_PARSER_ALTERNATIVE in cats


def test_critical_objection_blocks():
    classifier = ReviewerObjectionClassifier()
    cs = classifier.classify([
        {"objection_id": "o1",
         "text": "This risks a forbidden consciousness claim."}])
    c = cs[0]
    assert c.severity == ObjectionSeverity.CRITICAL
    assert c.blocks is True  # critical + open


def test_invalid_with_evidence_requires_refs():
    classifier = ReviewerObjectionClassifier()
    # Marked invalid_with_evidence but no evidence refs -> downgraded.
    c = classifier.classify_one(
        {"objection_id": "o1", "text": "x",
         "validity": ObjectionValidityStatus.INVALID_WITH_EVIDENCE})
    assert c.validity == ObjectionValidityStatus.REQUIRES_MORE_EVIDENCE
    # With refs, it stays invalid_with_evidence.
    c2 = classifier.classify_one(
        {"objection_id": "o2", "text": "x",
         "validity": ObjectionValidityStatus.INVALID_WITH_EVIDENCE,
         "evidence_refs": ["e1"]})
    assert c2.validity == ObjectionValidityStatus.INVALID_WITH_EVIDENCE


def test_not_dismissed_by_default():
    classifier = ReviewerObjectionClassifier()
    c = classifier.classify_one({"objection_id": "o1", "text": "vague concern"})
    assert c.to_dict()["dismissed_by_default"] is False
    assert c.open is True  # defaults to unresolved


def test_summary_counts():
    classifier = ReviewerObjectionClassifier()
    cs = classifier.classify([
        {"objection_id": "o1", "text": "forbidden consciousness risk"},
        {"objection_id": "o2", "text": "fixture overfit",
         "validity": ObjectionValidityStatus.VALID}])
    summary = ReviewerObjectionClassifier.summary(cs)
    assert summary["reviewer_objection_count"] == 2
    assert summary["critical_unresolved_count"] >= 1
    assert summary["valid_objection_count"] == 1
