"""Independent review <-> Research Baseline + Cycle: consumes; missing visible."""

from __future__ import annotations

from solaris_ai_nn.independent_review import IndependentReviewRuntime


def _sci():
    return {"claim_registry": {"scientific_claim_count": 1,
                               "supported_claim_count": 1, "claims": [
        {"claim_id": "c1", "text": "Signs form.", "category": "sensorium_claim",
         "status": "supported", "evidence_refs": ["e1"],
         "counterevidence_refs": []}]},
            "counterevidence": {"counterevidence_count": 0, "records": []},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": []}}


def test_consumes_research_baseline(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({"research_baseline": {"baseline_status": "validated",
                                          "safety_boundary_status": "pass"},
                    "replication": {"replication_arm_count": 3},
                    "safety": {"critical_regression_count": 0},
                    "scientific_claims": _sci(),
                    "sanitizer_inputs": {"a": "Signs form. Not conscious."}})
    rt.run()
    cats = [a["category"] for a in rt.manifest.to_dict()["artifacts"]
            if a["status"] == "present"]
    assert "research_baseline_report" in cats
    # Baseline status appears in the reviewer pack.
    assert rt.reviewer_pack["sections"]["baseline_under_review"] == "validated"


def test_consumes_research_cycle(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({"research_baseline": {"baseline_status": "validated",
                                          "safety_boundary_status": "pass"},
                    "research_cycle": {"current_cycle_stage": "blocked"},
                    "safety": {"critical_regression_count": 0},
                    "scientific_claims": _sci()})
    rt.run()
    cats = [a["category"] for a in rt.manifest.to_dict()["artifacts"]
            if a["status"] == "present"]
    assert "research_cycle_report" in cats


def test_missing_artifacts_visible(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    # No soak/replication/architecture -> those stay visible as missing.
    rt.load_bundle({"research_baseline": {"baseline_status": "validated",
                                          "safety_boundary_status": "pass"},
                    "safety": {"critical_regression_count": 0},
                    "scientific_claims": _sci()})
    rt.run()
    missing = [a["category"] for a in rt.manifest.to_dict()["artifacts"]
               if a["status"] == "missing"]
    assert "soak_dossier" in missing
    assert "replication_report" in missing
