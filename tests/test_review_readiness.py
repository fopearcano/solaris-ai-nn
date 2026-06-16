"""Review readiness: sanitizer/forbidden block; honest weak evidence ready."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    IndependentReviewReadinessEvaluator,
    ReviewReadinessStatus,
)


def _args(**overrides):
    base = dict(
        manifest={"missing_critical_artifact_count": 0},
        sanitizer={"blocks_readiness": False, "sanitizer_finding_count": 0,
                   "critical_sanitizer_finding_count": 0},
        claim_registry={"scientific_claim_count": 2, "supported_claim_count": 1,
                        "weakly_supported_claim_count": 1,
                        "partially_supported_claim_count": 0},
        forbidden={"asserted_forbidden_count": 0, "blocks_publication": False},
        adversarial={"strong_alternative_count": 0},
        audit_matrix={"audit_matrix_blocker_count": 0},
        response_ledger={"unresolved_objection_count": 0},
        challenges={"available_challenge_count": 5},
        safety_boundary_present=True)
    base.update(overrides)
    return base


def test_sanitizer_failure_blocks():
    r = IndependentReviewReadinessEvaluator().evaluate(**_args(
        sanitizer={"blocks_readiness": True,
                   "critical_sanitizer_finding_count": 1,
                   "sanitizer_finding_count": 1}))
    assert r.status == ReviewReadinessStatus.NOT_READY_SANITIZATION_FAILED


def test_forbidden_claim_blocks():
    r = IndependentReviewReadinessEvaluator().evaluate(**_args(
        forbidden={"asserted_forbidden_count": 1, "blocks_publication": True}))
    assert r.status == ReviewReadinessStatus.BLOCKED_BY_FORBIDDEN_CLAIMS


def test_missing_safety_boundary_blocks():
    r = IndependentReviewReadinessEvaluator().evaluate(**_args(
        safety_boundary_present=False))
    assert r.status == ReviewReadinessStatus.NOT_READY_SAFETY_BOUNDARY_MISSING


def test_clean_evidence_ready_for_hostile_review():
    r = IndependentReviewReadinessEvaluator().evaluate(**_args())
    assert r.status == ReviewReadinessStatus.READY_FOR_HOSTILE_EXTERNAL_REVIEW


def test_weak_honest_evidence_still_review_ready_with_limitations():
    # A single weakly-supported claim with a strong outstanding alternative
    # is still review-ready, just with major limitations.
    r = IndependentReviewReadinessEvaluator().evaluate(**_args(
        claim_registry={"scientific_claim_count": 1, "supported_claim_count": 0,
                        "weakly_supported_claim_count": 1,
                        "partially_supported_claim_count": 0},
        adversarial={"strong_alternative_count": 1}))
    assert r.status == ReviewReadinessStatus.READY_WITH_MAJOR_LIMITATIONS
    assert r.status not in (
        ReviewReadinessStatus.NOT_READY_CLAIMS_UNSUPPORTED,)
