"""Scientific claim reports: all generated, ClaimGuard-scanned, failures visible."""

from __future__ import annotations

import os

from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def _run(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3},
        "live_field": {"present": True},
        "claims": [
            {"claim_id": "c1", "text": "Signs form under fixtures.",
             "category": "sensorium_claim",
             "evidence": [{"evidence_id": "e1", "source": "semiogenesis",
                           "role": "supports"}],
             "factors": {"direct_evidence": True, "replication_evidence": True,
                         "control_comparison": True}},
            {"claim_id": "c2", "text": "Binding emerges everywhere.",
             "category": "sensorium_claim", "evidence": [],
             "missing_evidence_reason": "no experiment"},
            {"claim_id": "c3", "text": "A core claim was refuted.",
             "category": "falsification_claim",
             "evidence": [{"evidence_id": "e9",
                           "source": "replication_falsification",
                           "role": "falsifies"}],
             "factors": {"falsified_core": True}}]})
    rt.run()
    return rt


def test_all_reports_generated(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("SCIENTIFIC_CLAIM_REPORT.md", "SCIENTIFIC_CLAIM_REPORT.json",
                     "CLAIM_REGISTRY.md", "THEORY_LEDGER.md", "EVIDENCE_MAP.md",
                     "COUNTEREVIDENCE.md", "FORBIDDEN_CLAIMS.md",
                     "PUBLICATION_DOSSIER.md", "SAFE_ABSTRACTS.md",
                     "LIMITATIONS.md"):
        assert expected in names


def test_reports_claim_guard_scanned(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    assert report["claim_guard_safe"] is True


def test_unsupported_and_falsified_visible_in_report(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path), "SCIENTIFIC_CLAIM_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read()
    assert "Unsupported claims" in text
    assert "Contradicted / falsified claims" in text
    assert "What this does NOT do" in text
    assert "remain visible" in text.lower()


def test_disclaimers_in_report(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path), "SCIENTIFIC_CLAIM_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read()
    assert "does not prove consciousness" in text.lower()
    assert "no git or github operation occurred" in text.lower()
