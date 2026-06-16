"""Independent review <-> Soak/Replication/Falsification: builds challenges."""

from __future__ import annotations

from solaris_ai_nn.independent_review import IndependentReviewRuntime


def _sci():
    return {"claim_registry": {"scientific_claim_count": 1, "claims": [
        {"claim_id": "c1", "text": "x", "category": "developmental_claim",
         "status": "weakly_supported", "evidence_refs": ["e1"],
         "counterevidence_refs": []}]},
            "counterevidence": {"counterevidence_count": 0, "records": []},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": []}}


def test_consumes_soak_replication_falsification(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({"soak": {"x": 1}, "replication": {"replication_arm_count": 3},
                    "falsification": {"falsified_claim_count": 0},
                    "safety": {"critical_regression_count": 0},
                    "scientific_claims": _sci()})
    rt.run()
    cats = [a["category"] for a in rt.manifest.to_dict()["artifacts"]
            if a["status"] == "present"]
    assert "soak_dossier" in cats
    assert "replication_report" in cats
    assert "falsification_report" in cats


def test_builds_challenges_from_controls(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({"soak": {"x": 1}, "replication": {"replication_arm_count": 3},
                    "falsification": {"falsified_claim_count": 0},
                    "safety": {"critical_regression_count": 0},
                    "scientific_claims": _sci()})
    rt.run()
    available = [s["challenge_type"] for s in rt.challenges["steps"]
                 if s["status"] == "available"]
    assert "falsification_replay" in available
    assert "passive_parser_control_comparison" in available
    assert "shuffled_event_order_test" in available  # needs soak
