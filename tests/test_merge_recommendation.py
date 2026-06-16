"""Merge recommendation: recommend only with evidence; safety/tests block."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import MergeRecommendationBuilder
from solaris_ai_nn.implementation_intake.merge_recommendation import (
    MergeRecommendationStatus,
)


def _clean_inputs():
    return dict(
        manifest={"blockers": []},
        diff_audit={"blocker_count": 0, "warning_count": 0,
                    "forbidden_file_change_count": 0},
        spec_compliance={"counts": {"satisfied": 3}, "blocking_failure_count": 0},
        test_audit={"passes": True, "blockers": [], "warnings": []},
        safety_regression={"critical_count": 0, "major_count": 0},
        claimguard_audit={"blocks_readiness": False},
        coverage_matrix={"coverage_gap_count": 0})


def test_merge_recommended_only_with_sufficient_evidence():
    rec = MergeRecommendationBuilder().build(**_clean_inputs()).to_dict()
    assert rec["status"] == MergeRecommendationStatus.RECOMMEND_MERGE
    assert rec["advisory_only"] is True
    assert rec["merges_pr"] is False


def test_safety_failure_blocks():
    inp = _clean_inputs()
    inp["safety_regression"] = {"critical_count": 1, "major_count": 0}
    rec = MergeRecommendationBuilder().build(**inp).to_dict()
    assert rec["status"] == MergeRecommendationStatus.BLOCK_MERGE_DUE_TO_SAFETY


def test_tests_failure_blocks():
    inp = _clean_inputs()
    inp["test_audit"] = {"passes": False, "blockers": ["failed test"],
                         "warnings": []}
    rec = MergeRecommendationBuilder().build(**inp).to_dict()
    assert rec["status"] == MergeRecommendationStatus.BLOCK_MERGE_DUE_TO_TESTS


def test_missing_evidence_blocks():
    inp = _clean_inputs()
    inp["manifest"] = {"blockers": ["safety_gates", "test_results"]}
    rec = MergeRecommendationBuilder().build(**inp).to_dict()
    assert rec["status"] == \
        MergeRecommendationStatus.BLOCK_MERGE_DUE_TO_MISSING_EVIDENCE


def test_inconclusive_without_evidence():
    rec = MergeRecommendationBuilder().build().to_dict()
    assert rec["status"] == MergeRecommendationStatus.INCONCLUSIVE


def test_coverage_gap_recommends_revisions():
    inp = _clean_inputs()
    inp["coverage_matrix"] = {"coverage_gap_count": 2}
    rec = MergeRecommendationBuilder().build(**inp).to_dict()
    assert rec["status"] == MergeRecommendationStatus.RECOMMEND_REVISIONS
