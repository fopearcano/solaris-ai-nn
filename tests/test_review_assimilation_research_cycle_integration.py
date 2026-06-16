"""Review assimilation <-> Research Cycle: gaps become blockers; queue -> actions."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def _run(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form.", "status": "supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": [
            {"objection_id": "o1",
             "text": "This risks a forbidden consciousness claim.",
             "severity": "critical", "claim_refs": ["c1"]},
            {"objection_id": "o2", "text": "No control arm.",
             "claim_refs": ["c1"]}],
        "missing_artifacts": ["soak_dossier"]})
    rt.run()
    return rt


def test_evidence_gaps_become_cycle_blockers(tmp_path):
    rt = _run(tmp_path)
    cycle = rt.research_cycle_inputs()
    assert cycle["evidence_gaps"]
    assert cycle["unresolved_critical_objection_count"] >= 1
    assert cycle["publication_blocked"] is True


def test_review_queue_becomes_next_actions(tmp_path):
    rt = _run(tmp_path)
    cycle = rt.research_cycle_inputs()
    assert cycle["review_queue"]
    # The queue preserves an unresolved/open item for the critical objection.
    assert any(i["open"] for i in cycle["review_queue"])
