"""Independent review reports: all generated, ClaimGuard-scanned, no-publish."""

from __future__ import annotations

import os

from solaris_ai_nn.independent_review import IndependentReviewRuntime


def _run(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3},
        "falsification": {"falsified_claim_count": 1},
        "safety": {"critical_regression_count": 0},
        "scientific_claims": {
            "claim_registry": {"scientific_claim_count": 2,
                               "supported_claim_count": 1, "claims": [
                {"claim_id": "c1", "text": "Signs form.",
                 "category": "sensorium_claim", "status": "supported",
                 "evidence_refs": ["e1"], "counterevidence_refs": []},
                {"claim_id": "c2", "text": "Refuted.",
                 "category": "falsification_claim", "status": "falsified",
                 "evidence_refs": ["e2"], "counterevidence_refs": ["ce1"]}]},
            "counterevidence": {"counterevidence_count": 1, "records": [
                {"counter_type": "falsification_failure", "detail": "refuted",
                 "blocks_claim": True}]},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": [
                {"category": "no_consciousness_evidence",
                 "text": "no consciousness evidence"}]}},
        "sanitizer_inputs": {"abstract": "Signs form. It is not conscious."},
        "objections": [{"objection_id": "o1", "text": "overfit?",
                        "status": "unresolved"}]})
    rt.run()
    return rt


def test_all_reports_generated(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("INDEPENDENT_REVIEW_REPORT.md",
                     "INDEPENDENT_REVIEW_REPORT.json", "REVIEW_MANIFEST.md",
                     "SANITIZATION_REPORT.md", "REVIEWER_PACK.md",
                     "REPRODUCIBILITY_CHALLENGE.md", "REVIEW_PROTOCOL.md",
                     "REVIEWER_QUESTIONS.md", "ADVERSARIAL_REVIEW.md",
                     "AUDIT_MATRIX.md", "RESPONSE_LEDGER.md",
                     "REVIEW_READINESS.md"):
        assert expected in names


def test_reports_claim_guard_scanned(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    assert report["claim_guard_safe"] is True


def test_no_publish_disclaimer_present(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path), "INDEPENDENT_REVIEW_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "no artifacts were published" in text
    assert "no files were uploaded" in text
    assert "no git or github operation occurred" in text
    assert "no external reviewer was contacted" in text
