"""Claim impact: downgraded, falsified, forbidden risk blocks readiness."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    ClaimImpactAssessor,
    ClaimImpactType,
    ObjectionValidityStatus,
    ReviewerObjectionClassifier,
)


def _classify(objections):
    return ReviewerObjectionClassifier().classify(objections)


def test_claim_downgraded():
    objs = _classify([
        {"objection_id": "o1", "text": "Probably fixture overfit.",
         "claim_refs": ["c1"]}])
    impacts = ClaimImpactAssessor().assess(objections=objs)
    assert any(i.claim_id == "c1" and i.is_downgrade for i in impacts)


def test_claim_marked_falsified():
    objs = _classify([
        {"objection_id": "o1", "text": "Replication refuted this.",
         "claim_refs": ["c1"],
         "validity": ObjectionValidityStatus.ACCEPTED_AS_FALSIFICATION}])
    impacts = ClaimImpactAssessor().assess(objections=objs)
    assert any(i.impact_type == ClaimImpactType.MARK_FALSIFIED for i in impacts)
    summary = ClaimImpactAssessor.summary(impacts)
    assert summary["claim_falsification_count"] >= 1


def test_forbidden_risk_blocks_readiness():
    objs = _classify([
        {"objection_id": "o1",
         "text": "This risks a forbidden consciousness claim.",
         "claim_refs": ["c2"]}])
    impacts = ClaimImpactAssessor().assess(objections=objs)
    summary = ClaimImpactAssessor.summary(impacts)
    assert summary["claim_forbidden_count"] >= 1
    assert summary["blocks_readiness"] is True


def test_impacts_reference_claim_ids():
    objs = _classify([
        {"objection_id": "o1", "text": "unsupported claim", "claim_refs": ["c9"]}])
    impacts = ClaimImpactAssessor().assess(objections=objs)
    assert all(i.claim_id == "c9" for i in impacts)


def test_failed_reproduction_downgrades():
    from solaris_ai_nn.review_assimilation import (
        ReviewerReproductionOutcomeIngestor)

    outcomes = ReviewerReproductionOutcomeIngestor().ingest([
        {"challenge_type": "falsification_replay", "status": "not_reproduced",
         "claim_refs": ["c1"]}])
    impacts = ClaimImpactAssessor().assess(objections=[], reproductions=outcomes)
    assert any(i.impact_type == ClaimImpactType.DOWNGRADE_TO_INCONCLUSIVE
               for i in impacts)


def test_impact_is_proposal():
    objs = _classify([{"objection_id": "o1", "text": "weak evidence",
                       "claim_refs": ["c1"]}])
    impacts = ClaimImpactAssessor().assess(objections=objs)
    assert all(i.to_dict()["is_proposal"] is True for i in impacts)
