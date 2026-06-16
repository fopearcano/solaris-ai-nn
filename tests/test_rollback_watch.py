"""Rollback watch: recommendation created, not executed, evidence preserved."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    RollbackWatch,
    RollbackWatchRecommendation,
    RollbackWatchTrigger,
)


def test_rollback_recommendation_created():
    result = RollbackWatch().build(
        regression={"critical_regression_count": 1},
        evidence={"safety_negative": True},
        intake={"forbidden_file_change_count": 1}).to_dict()
    assert result["recommendation"] == \
        RollbackWatchRecommendation.ROLLBACK_RECOMMENDED
    assert RollbackWatchTrigger.CRITICAL_SAFETY_REGRESSION in result["triggers"]


def test_rollback_not_executed():
    result = RollbackWatch().build(
        regression={"critical_regression_count": 1},
        evidence={"safety_negative": True}).to_dict()
    assert result["executed"] is False
    assert result["preserves_evidence"] is True


def test_evidence_preserved_in_steps():
    result = RollbackWatch().build(
        regression={"critical_regression_count": 1},
        evidence={"safety_negative": True})
    joined = " ".join(result.steps).lower()
    assert "do not delete" in joined


def test_no_rollback_when_clean():
    result = RollbackWatch().build(
        regression={"critical_regression_count": 0,
                    "major_regression_count": 0},
        evidence={"safety_negative": False}, intake={},
        validation={"missing_validation_artifact_count": 0}).to_dict()
    assert result["recommendation"] == \
        RollbackWatchRecommendation.NO_ROLLBACK_NEEDED
    assert result["rollback_watch_trigger_count"] == 0


def test_failed_tests_request_revision():
    result = RollbackWatch().build(
        regression={"critical_regression_count": 0},
        evidence={"safety_negative": False},
        intake={"test_failure_count": 2}).to_dict()
    assert result["recommendation"] == \
        RollbackWatchRecommendation.REQUEST_REVISION
