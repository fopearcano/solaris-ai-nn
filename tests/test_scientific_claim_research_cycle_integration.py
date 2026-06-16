"""Scientific claims <-> Research Cycle: consumes evidence; blocked cycle limits."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def _claim_spec(strong=True):
    factors = ({"direct_evidence": True, "replication_evidence": True,
                "control_comparison": True} if strong
               else {"direct_evidence": True})
    return {"claim_id": "c1", "text": "Signs form under fixtures.",
            "category": "sensorium_claim",
            "evidence": [{"evidence_id": "e1", "source": "research_cycle",
                          "role": "supports"}],
            "factors": factors}


def test_consumes_evidence_ledger(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_cycle": {"current_cycle_stage": "research_baseline_validated",
                           "evidence_ledger_entry_count": 10},
        "replication": {"replication_arm_count": 3},
        "claims": [_claim_spec()]})
    rt.run()
    # Evidence sourced from the research cycle is mapped.
    assert rt.evidence_map.evidence_mapping_count == 1
    assert rt.scientific_claims_status()["supported_claim_count"] == 1


def test_blocked_cycle_constrains_claims(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_cycle": {"current_cycle_stage": "blocked"},
        "implementation_intake": {"critical_safety_regression_count": 1},
        "claims": [_claim_spec()]})
    rt.run()
    # A safety regression in the cycle blocks the publishable claim's strength.
    st = rt.scientific_claims_status()
    assert st["supported_claim_count"] == 0
    assert st["publication_readiness_status"] in (
        "blocked_by_safety", "blocked_by_counterevidence")
