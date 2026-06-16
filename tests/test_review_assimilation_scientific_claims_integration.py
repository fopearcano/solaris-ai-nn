"""Review assimilation <-> Scientific Claims: proposals, counterevidence, forbidden."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def _run(tmp_path, forbidden=False):
    objections = [
        {"objection_id": "o1", "text": "Probably fixture overfit.",
         "claim_refs": ["c1"]}]
    if forbidden:
        objections.append(
            {"objection_id": "o2",
             "text": "This risks a forbidden consciousness claim.",
             "severity": "critical", "claim_refs": ["c2"]})
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form.", "status": "supported"},
                {"claim_id": "c2", "text": "Binding emerges.",
                 "status": "weakly_supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": objections})
    rt.run()
    return rt


def test_sends_claim_revision_proposals(tmp_path):
    rt = _run(tmp_path)
    proposals = rt.scientific_claims_proposals()
    assert proposals["claim_revision_proposals"]
    assert proposals["claim_impacts"]


def test_sends_counterevidence_and_impacts(tmp_path):
    rt = _run(tmp_path)
    # Claim impacts reference the claim and are proposals only.
    impacts = rt.scientific_claims_proposals()["claim_impacts"]
    assert any(i["claim_id"] == "c1" for i in impacts)
    assert all(i["is_proposal"] for i in impacts)


def test_forbidden_risks_visible(tmp_path):
    rt = _run(tmp_path, forbidden=True)
    proposals = rt.scientific_claims_proposals()
    assert proposals["forbidden_claim_risk"] is True
    # Publication readiness is blocked.
    assert proposals["publication_readiness_revision"][
        "publication_readiness_impact"] == "block_publication"
