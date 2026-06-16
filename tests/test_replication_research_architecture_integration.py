"""Replication: research protocols exist; arch consumes outputs; falsified blocks."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import replication_revision_proposals
from solaris_ai_nn.architecture_evolution.evidence_mapper import EVIDENCE_SOURCES
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_research_protocols_exist():
    for name in ("developmental_replication_protocol",
                 "cross_run_alignment_protocol",
                 "structural_similarity_protocol",
                 "divergence_analysis_protocol",
                 "environmental_dependency_protocol",
                 "falsification_lab_protocol",
                 "replication_matrix_protocol"):
        assert name in PROTOCOLS


def test_evidence_sources_include_replication():
    assert "replication_report" in EVIDENCE_SOURCES
    assert "replication_matrix" in EVIDENCE_SOURCES
    assert "falsification_report" in EVIDENCE_SOURCES


def test_architecture_consumes_replication_outputs():
    proposals = replication_revision_proposals({
        "replicated_claim_count": 5, "falsified_claim_count": 0,
        "diverged_claim_count": 0})
    assert any(p["target"] == "promote_stable_modules" for p in proposals)
    assert all(p["advisory_only"] for p in proposals)


def test_falsified_claims_block_promotion():
    proposals = replication_revision_proposals({
        "falsified_claim_count": 2, "replicated_claim_count": 3})
    freeze = next(p for p in proposals
                  if p["target"] == "freeze_unsupported_claims")
    assert freeze.get("blocks_promotion") is True
    # With a falsified claim present, promotion is NOT proposed.
    assert not any(p["target"] == "promote_stable_modules" for p in proposals)
