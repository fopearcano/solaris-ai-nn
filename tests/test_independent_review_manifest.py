"""Independent review manifest: serialization, missing visible, negatives kept."""

from __future__ import annotations

import os

from solaris_ai_nn.independent_review import (
    IndependentReviewManifest,
    ReviewArtifact,
    ReviewArtifactStatus,
)


def test_manifest_serializes(tmp_path):
    man = IndependentReviewManifest(state_dir=str(tmp_path))
    man.add(ReviewArtifact(category="scientific_claim_report", ref="sci",
                           status=ReviewArtifactStatus.PRESENT))
    d = man.to_dict()
    assert d["independent_review_artifact_count"] == 1
    assert d["uploads"] is False
    assert d["artifacts"][0]["uploaded"] is False


def test_missing_artifacts_visible(tmp_path):
    man = IndependentReviewManifest(state_dir=str(tmp_path))
    man.add_missing("replication_report")
    man.add(ReviewArtifact(category="claim_registry", ref="cr"))
    assert len(man.missing()) == 1
    assert man.index()["missing_review_artifact_count"] == 1


def test_negative_falsified_included(tmp_path):
    man = IndependentReviewManifest(state_dir=str(tmp_path))
    man.add(ReviewArtifact(category="falsification_report", ref="f",
                           is_negative_or_falsified=True))
    man.add(ReviewArtifact(category="counterevidence_report", ref="ce",
                           is_negative_or_falsified=True))
    assert len(man.negative_or_falsified()) == 2


def test_missing_critical_tracked(tmp_path):
    man = IndependentReviewManifest(state_dir=str(tmp_path))
    man.add_missing("scientific_claim_report")  # critical
    man.add_missing("fixture_data")             # not critical
    assert len(man.missing_critical()) == 1


def test_persist_writes_files(tmp_path):
    man = IndependentReviewManifest(state_dir=str(tmp_path))
    man.add(ReviewArtifact(category="claim_registry", ref="cr"))
    paths = man.persist_manifest()
    assert os.path.isfile(paths["manifest"])
    assert os.path.isfile(paths["index"])
