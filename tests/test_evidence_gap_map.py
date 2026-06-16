"""Evidence gap map: gaps mapped to claims, critical block, become recommendations."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    EvidenceGapCategory,
    ReviewDrivenExperimentRecommender,
    ReviewEvidenceGapMapBuilder,
    ReviewerObjectionClassifier,
)


def _classify(objections):
    return ReviewerObjectionClassifier().classify(objections)


def test_gaps_mapped_to_claims():
    objs = _classify([
        {"objection_id": "o1", "text": "There is no control arm.",
         "claim_refs": ["c1"]}])
    gap_map = ReviewEvidenceGapMapBuilder().build(objections=objs)
    assert any(g.category == EvidenceGapCategory.MISSING_CONTROL
               and "c1" in g.claim_refs for g in gap_map.gaps)


def test_critical_gaps_block_readiness():
    objs = _classify([
        {"objection_id": "o1", "text": "The safety boundary is unverified.",
         "severity": "critical", "claim_refs": ["c1"]}])
    gap_map = ReviewEvidenceGapMapBuilder().build(objections=objs)
    assert gap_map.to_dict()["critical_evidence_gap_count"] >= 1
    assert any(g.blocks_readiness for g in gap_map.gaps)


def test_gaps_become_recommendations():
    objs = _classify([
        {"objection_id": "o1", "text": "No control arm.", "claim_refs": ["c1"]}])
    gap_map = ReviewEvidenceGapMapBuilder().build(objections=objs)
    recs = ReviewDrivenExperimentRecommender().recommend(
        objections=[], gaps=gap_map.gaps)
    assert recs  # a control gap becomes an add-control-arm recommendation


def test_missing_artifacts_become_gaps():
    gap_map = ReviewEvidenceGapMapBuilder().build(
        objections=[], missing_artifacts=["soak_dossier"])
    assert gap_map.to_dict()["evidence_gap_count"] >= 1
