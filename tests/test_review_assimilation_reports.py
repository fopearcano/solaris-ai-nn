"""Review assimilation reports: all generated, ClaimGuard-scanned, disclaimers."""

from __future__ import annotations

import os

from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def _run(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "independent_review": {
            "response_ledger": {"objections": [
                {"objection_id": "o_led", "text": "No live replication.",
                 "status": "unresolved", "claim_refs": ["c1"]}]},
            "review_readiness": {
                "review_readiness_status": "ready_for_internal_review"}},
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form.", "status": "supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": [
            {"objection_id": "o1", "text": "Probably fixture overfit.",
             "claim_refs": ["c1"]},
            {"objection_id": "o2", "text": "Replication refuted this.",
             "validity": "accepted_as_falsification", "claim_refs": ["c1"]}],
        "reproduction_outcomes": [
            {"challenge_type": "falsification_replay", "status": "not_reproduced",
             "failure_reason": "missing_fixture", "claim_refs": ["c1"]}],
        "missing_artifacts": ["soak_dossier"]})
    rt.run()
    return rt


def test_all_reports_generated(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("REVIEW_ASSIMILATION_REPORT.md",
                     "REVIEW_ASSIMILATION_REPORT.json", "FEEDBACK_MANIFEST.md",
                     "OBJECTION_CLASSIFICATION.md", "REPRODUCTION_OUTCOMES.md",
                     "CLAIM_IMPACT.md", "THEORY_IMPACT.md", "EVIDENCE_GAP_MAP.md",
                     "EXPERIMENT_RECOMMENDATIONS.md",
                     "CLAIM_REVISION_PROPOSALS.md",
                     "PUBLICATION_READINESS_REVISION.md", "REVIEW_QUEUE.md"):
        assert expected in names


def test_reports_claim_guard_scanned(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    assert report["claim_guard_safe"] is True


def test_no_training_no_publication_disclaimer_present(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path), "REVIEW_ASSIMILATION_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "not as model training" in text
    assert "no publication occurred" in text
    assert "no reviewer was contacted" in text
    assert "no git or github operation occurred" in text
