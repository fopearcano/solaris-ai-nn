"""Rollback recommendation: generated, never executes, evidence preserved."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import RollbackRecommendationBuilder
from solaris_ai_nn.implementation_intake.rollback_recommendation import (
    RollbackRecommendationReason,
    RollbackUrgency,
)


def test_rollback_recommendation_generated():
    rec = RollbackRecommendationBuilder().build(
        safety_regression={"critical_count": 1},
        merge_recommendation={"status": "block_merge_due_to_safety"}).to_dict()
    assert rec["recommended"] is True
    assert RollbackRecommendationReason.SAFETY_REGRESSION in rec["reasons"]
    assert rec["urgency"] == RollbackUrgency.IMMEDIATE


def test_rollback_does_not_execute():
    rec = RollbackRecommendationBuilder().build(
        test_audit={"passes": False}).to_dict()
    assert rec["executed"] is False
    assert rec["preserves_evidence"] is True


def test_evidence_preserved_in_steps():
    rec = RollbackRecommendationBuilder().build(
        test_audit={"passes": False})
    joined = " ".join(rec.steps).lower()
    assert "do not delete" in joined
    assert "evidence" in joined


def test_not_recommended_when_clean():
    rec = RollbackRecommendationBuilder().build(
        merge_recommendation={"status": "recommend_merge"},
        safety_regression={"critical_count": 0},
        test_audit={"passes": True},
        spec_compliance={"blocking_failure_count": 0},
        diff_audit={"forbidden_file_change_count": 0,
                    "unexpected_file_change_count": 0},
        claimguard_audit={"blocks_readiness": False},
        manifest={"blockers": []}).to_dict()
    assert rec["recommended"] is False
    assert rec["urgency"] == RollbackUrgency.NONE
