"""Review assimilation <-> Independent Review: consumes ledger/adversarial/matrix."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def _bundle():
    return {
        "independent_review": {
            "response_ledger": {"objections": [
                {"objection_id": "o_led",
                 "text": "No live-field replication is shown.",
                 "status": "unresolved", "claim_refs": ["c1"]}]},
            "adversarial_findings": {"explanations": [
                {"explanation_type": "fixture_overfit", "strong": True}]},
            "audit_matrix": {"audit_matrix_blocker_count": 1},
            "review_readiness": {
                "review_readiness_status": "ready_for_internal_review"}},
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form.", "status": "supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
    }


def test_consumes_response_ledger():
    rt = ReviewerFeedbackAssimilationRuntime(state_dir="/tmp/ra_irint1")
    rt.load_bundle(_bundle())
    rt.run()
    # The response-ledger objection is classified.
    ids = {c["objection_id"] for c in
           rt.objections["classifications"]}
    assert "o_led" in ids


def test_consumes_adversarial_review():
    rt = ReviewerFeedbackAssimilationRuntime(state_dir="/tmp/ra_irint2")
    rt.load_bundle(_bundle())
    rt.run()
    # The adversarial finding is indexed in the feedback manifest.
    sources = {a["source_type"] for a in rt.manifest.to_dict()["artifacts"]}
    assert "adversarial_review_finding" in sources


def test_consumes_audit_matrix():
    rt = ReviewerFeedbackAssimilationRuntime(state_dir="/tmp/ra_irint3")
    rt.load_bundle(_bundle())
    rt.run()
    sources = {a["source_type"] for a in rt.manifest.to_dict()["artifacts"]}
    assert "audit_matrix_blocker" in sources
