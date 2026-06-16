"""Audit matrix: created, gaps visible, no empty green dashboard."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    AuditMatrixStatus,
    IndependentReviewAuditMatrix,
)


def _claims():
    return [
        {"claim_id": "c1", "text": "Signs form.", "category": "sensorium_claim",
         "status": "supported", "evidence_refs": ["e1"],
         "counterevidence_refs": []},
        {"claim_id": "c2", "text": "Binding everywhere.",
         "category": "sensorium_claim", "status": "unsupported",
         "evidence_refs": [], "counterevidence_refs": []},
        {"claim_id": "c3", "text": "Refuted claim.",
         "category": "falsification_claim", "status": "falsified",
         "evidence_refs": ["e9"], "counterevidence_refs": ["ce1"]}]


def test_matrix_created():
    m = IndependentReviewAuditMatrix().build(
        claims=_claims(), counterevidence={"records": []},
        limitations={"limitations": []}).to_dict()
    assert m["audit_matrix_row_count"] == 3


def test_gaps_visible_no_green_dashboard():
    m = IndependentReviewAuditMatrix().build(
        claims=_claims(), counterevidence={"records": []},
        limitations={"limitations": []}).to_dict()
    statuses = {r["status"] for r in m["rows"]}
    # Not all rows are "reviewable" -- gaps are exposed.
    assert AuditMatrixStatus.REVIEWABLE in statuses
    assert AuditMatrixStatus.MISSING_EVIDENCE in statuses
    assert AuditMatrixStatus.FALSIFIED in statuses


def test_falsified_unsupported_flagged_as_blockers():
    m = IndependentReviewAuditMatrix().build(
        claims=_claims(), counterevidence={"records": []},
        limitations={"limitations": []}).to_dict()
    assert m["audit_matrix_blocker_count"] >= 2  # unsupported + falsified


def test_rows_link_evidence_and_counterevidence():
    matrix = IndependentReviewAuditMatrix().build(
        claims=_claims(),
        counterevidence={"records": [{"counter_type": "fixture_overfit"}]},
        limitations={"limitations": [{"text": "no replication"}]})
    row = [r for r in matrix.rows if r.claim_id == "c1"][0]
    assert row.supporting_evidence == ["e1"]
    assert row.required_artifacts
