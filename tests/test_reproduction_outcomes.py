"""Reproduction outcomes: success/failure/partial/inconclusive; limitation; no mind."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    ReproductionOutcomeStatus,
    ReviewerReproductionOutcomeIngestor,
)


def test_all_outcome_statuses():
    ingestor = ReviewerReproductionOutcomeIngestor()
    outcomes = ingestor.ingest([
        {"challenge_type": "a", "status": "reproduced"},
        {"challenge_type": "b", "status": "partially_reproduced"},
        {"challenge_type": "c", "status": "not_reproduced"},
        {"challenge_type": "d", "status": "inconclusive"}])
    summary = ReviewerReproductionOutcomeIngestor.summary(outcomes)
    assert summary["reproduction_success_count"] == 2  # reproduced + partial
    assert summary["reproduction_failure_count"] == 1


def test_missing_artifact_is_project_limitation():
    ingestor = ReviewerReproductionOutcomeIngestor()
    outcomes = ingestor.ingest([
        {"challenge_type": "a",
         "status": "blocked_by_missing_artifact",
         "failure_reason": "missing_fixture"}])
    assert outcomes[0].is_project_limitation is True
    # A missing artifact is not counted as a reviewer failure.
    assert outcomes[0].is_failure is False


def test_no_consciousness_implication():
    ingestor = ReviewerReproductionOutcomeIngestor()
    outcomes = ingestor.ingest([
        {"challenge_type": "a", "status": "reproduced"}])
    assert outcomes[0].to_dict()["proves_consciousness"] is False


def test_outcome_is_evidence():
    ingestor = ReviewerReproductionOutcomeIngestor()
    outcomes = ingestor.ingest([
        {"challenge_type": "a", "status": "not_reproduced"}])
    assert outcomes[0].to_dict()["is_evidence"] is True
