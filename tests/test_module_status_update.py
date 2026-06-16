"""Module status update: promote, regression-watch, block-due-to-safety."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    ModuleStatusUpdateRecommendationBuilder,
    ModuleStatusUpdateType,
)


def _build(**kw):
    return ModuleStatusUpdateRecommendationBuilder().build(**kw).to_dict()


def test_validate_candidate_recommendation():
    rec = _build(
        evidence={"safety_negative": False, "counts": {"inconclusive": 0}},
        regression={"critical_regression_count": 0,
                    "major_regression_count": 0},
        comparison={"overall": "improved", "safety_regressed": False},
        intake={"spec_compliance_status": "satisfied", "test_failure_count": 0},
        validation={"artifacts": [
            {"artifact_type": "full_test_run", "present": True, "passed": True},
            {"artifact_type": "mini_soak", "present": True, "passed": True}],
            "missing_validation_artifact_count": 0})
    assert rec["update_type"] in (ModuleStatusUpdateType.VALIDATE_CANDIDATE,
                                  ModuleStatusUpdateType.PROMOTE_CANDIDATE)
    assert rec["metadata_only"] is True
    assert rec["modifies_source"] is False


def test_regression_watch_recommendation():
    rec = _build(
        evidence={"safety_negative": False},
        regression={"critical_regression_count": 0,
                    "major_regression_count": 1},
        comparison={"overall": "mixed", "safety_regressed": False},
        intake={"test_failure_count": 0},
        validation={"artifacts": [
            {"artifact_type": "full_test_run", "present": True, "passed": True}],
            "missing_validation_artifact_count": 0})
    assert rec["update_type"] == ModuleStatusUpdateType.REGRESSION_WATCH


def test_block_due_to_safety_recommendation():
    rec = _build(
        evidence={"safety_negative": True},
        regression={"critical_regression_count": 1},
        comparison={"overall": "regressed", "safety_regressed": True},
        intake={"merge_recommendation_status": "block_merge_due_to_safety"},
        validation={"artifacts": [], "missing_validation_artifact_count": 3})
    assert rec["update_type"] == ModuleStatusUpdateType.BLOCK_DUE_TO_SAFETY


def test_retest_when_evidence_missing():
    rec = _build(
        evidence={"safety_negative": False},
        regression={"critical_regression_count": 0,
                    "major_regression_count": 0},
        comparison={"overall": "unchanged", "safety_regressed": False},
        intake={"test_failure_count": 0},
        validation={"artifacts": [], "missing_validation_artifact_count": 2})
    assert rec["update_type"] == ModuleStatusUpdateType.RETEST_REQUIRED
