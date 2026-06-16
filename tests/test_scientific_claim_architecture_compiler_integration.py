"""Scientific claims <-> Architecture/Compiler: gaps -> experiments; falsified."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def test_claim_gaps_produce_experiment_suggestions(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "missing_live_data": True,
        "sensorium_differentiation": {"fixture_overfit_risk": True,
                                      "label_contamination_risk": True},
        "replication": {"failed_replication_count": 1},
        "claims": [{"claim_id": "c1", "text": "Signs form.",
                    "category": "sensorium_claim",
                    "evidence": [{"evidence_id": "e1", "source": "semiogenesis",
                                  "role": "weakly_supports"}],
                    "factors": {"direct_evidence": True}}]})
    rt.run()
    suggestions = {s["experiment"] for s in rt.experiment_suggestions()}
    assert "live_field_evidence_experiment" in suggestions
    assert "falsification_control_pack" in suggestions
    assert "contamination_mitigation_experiment" in suggestions


def test_falsified_claims_block_architecture_promotion_marker(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "falsification": {"falsified_claim_count": 1},
        "claims": [{"claim_id": "c1", "text": "Variant X improves cognition.",
                    "category": "architecture_claim",
                    "evidence": [{"evidence_id": "e1",
                                  "source": "architecture_evolution",
                                  "role": "falsifies"}],
                    "factors": {"direct_evidence": True, "falsified_core": True}}]})
    rt.run()
    # A falsified architecture claim is preserved and not publishable.
    assert rt.scientific_claims_status()["falsified_claim_count"] >= 1
    assert rt.scientific_claims_status()["supported_claim_count"] == 0
    # The dossier readiness is not "ready_as_preprint_draft".
    assert rt.dossier["publication_readiness_status"] != "ready_as_preprint_draft"
