"""Validation ingest: artifact ingested, missing required blocks, no execution."""

from __future__ import annotations

import inspect

from solaris_ai_nn.post_merge_assimilation import (
    PostMergeValidationIngest,
    ValidationArtifactType,
)
from solaris_ai_nn.post_merge_assimilation import validation_ingest


def test_validation_artifact_ingested():
    result = PostMergeValidationIngest().ingest({
        "full_test_run": {"passed": True},
        "safety_invariant_run": {"passed": True},
        "claimguard_run": {"safe": True}}).to_dict()
    assert result["validation_artifact_count"] >= 3
    test_run = next(a for a in result["artifacts"]
                    if a["artifact_type"] == ValidationArtifactType.FULL_TEST_RUN)
    assert test_run["passed"] is True


def test_missing_required_artifact_blocks():
    result = PostMergeValidationIngest().ingest({
        "full_test_run": {"passed": True}}).to_dict()
    # safety_invariant_run and claimguard_run missing -> required-missing.
    assert "safety_invariant_run" in result["missing_required"]
    assert "claimguard_run" in result["missing_required"]
    assert result["missing_validation_artifact_count"] >= 2


def test_failed_validation_recorded():
    result = PostMergeValidationIngest().ingest({
        "full_test_run": {"passed": False}}).to_dict()
    assert "full_test_run" in result["failed_validation"]


def test_no_validation_executed():
    src = inspect.getsource(validation_ingest)
    assert "subprocess" not in src
    assert "pytest" not in src.lower() or "run pytest" not in src.lower()
    result = PostMergeValidationIngest().ingest({}).to_dict()
    assert "no validation command is executed" in result["note"]
