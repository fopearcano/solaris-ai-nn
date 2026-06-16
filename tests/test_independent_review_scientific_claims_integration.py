"""Independent review <-> Scientific Claims: consumes registry; forbidden blocks."""

from __future__ import annotations

from solaris_ai_nn.independent_review import IndependentReviewRuntime


def _bundle(forbidden=False, counter=False):
    claims = [{"claim_id": "c1", "text": "Signs form.",
               "category": "sensorium_claim", "status": "supported",
               "evidence_refs": ["e1"], "counterevidence_refs": []}]
    records = ([{"counter_type": "fixture_overfit", "detail": "maybe overfit",
                 "blocks_claim": False}] if counter else [])
    return {
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3},
        "safety": {"critical_regression_count": 0},
        "scientific_claims": {
            "claim_registry": {"scientific_claim_count": 1,
                               "supported_claim_count": 1, "claims": claims},
            "counterevidence": {"counterevidence_count": len(records),
                                "records": records},
            "forbidden_claims": {
                "asserted_forbidden_count": 1 if forbidden else 0,
                "blocks_publication": forbidden},
            "limitations": {"limitation_count": 4, "limitations": []}},
        "sanitizer_inputs": {"abstract": "Signs form. It is not conscious."}}


def test_consumes_claim_registry(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    # Claims become audit-matrix rows.
    assert rt.audit_matrix["audit_matrix_row_count"] == 1


def test_forbidden_claims_block_readiness(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle(forbidden=True))
    rt.run()
    assert rt.independent_review_status()["review_readiness_status"] == \
        "blocked_by_forbidden_claims"


def test_counterevidence_included(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle(counter=True))
    rt.run()
    pack = rt.reviewer_pack["sections"]
    assert pack["counterevidence_table"]
