"""Reviewer feedback manifest: serialization, negatives preserved, missing visible."""

from __future__ import annotations

import os

from solaris_ai_nn.review_assimilation import (
    FeedbackSourceType,
    ReviewerFeedbackArtifact,
    ReviewerFeedbackManifest,
)


def test_manifest_serializes(tmp_path):
    man = ReviewerFeedbackManifest(state_dir=str(tmp_path))
    man.add(ReviewerFeedbackArtifact(
        source_type=FeedbackSourceType.REVIEWER_OBJECTION, ref="o1",
        summary="overfit?"))
    d = man.to_dict()
    assert d["reviewer_feedback_artifact_count"] == 1
    assert d["uploads"] is False
    assert d["artifacts"][0]["uploaded"] is False


def test_negative_feedback_preserved(tmp_path):
    man = ReviewerFeedbackManifest(state_dir=str(tmp_path))
    man.add(ReviewerFeedbackArtifact(
        source_type=FeedbackSourceType.FAILED_REPRODUCTION, ref="r1"))
    man.add(ReviewerFeedbackArtifact(
        source_type=FeedbackSourceType.ADVERSARIAL_REVIEW_FINDING, ref="a1"))
    assert len(man.negative()) == 2
    assert man.index()["negative_feedback_count"] == 2


def test_missing_feedback_visible(tmp_path):
    man = ReviewerFeedbackManifest(state_dir=str(tmp_path))
    man.add_missing(FeedbackSourceType.RESPONSE_LEDGER_ENTRY)
    assert len(man.missing()) == 1
    assert man.index()["missing_feedback_count"] == 1


def test_reviewer_identity_anonymized(tmp_path):
    man = ReviewerFeedbackManifest(state_dir=str(tmp_path), anonymize=True)
    a = man.add(ReviewerFeedbackArtifact(
        source_type=FeedbackSourceType.REVIEWER_OBJECTION,
        reviewer_id="alice@example.com"))
    assert a.reviewer_id == ""


def test_persist_writes_files(tmp_path):
    man = ReviewerFeedbackManifest(state_dir=str(tmp_path))
    man.add(ReviewerFeedbackArtifact(
        source_type=FeedbackSourceType.OPERATOR_NOTE))
    paths = man.persist_manifest()
    assert os.path.isfile(paths["manifest"])
    assert os.path.isfile(paths["index"])
