"""Scientific claims <-> Soak/Replication: replication strengthens, falsify blocks."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import ClaimStatus, ScientificClaimRuntime


def _claim(factors):
    return {"claim_id": "c1", "text": "Developmental pattern persists.",
            "category": "developmental_claim",
            "evidence": [{"evidence_id": "e1", "source": "developmental_soak",
                          "role": "supports"}],
            "factors": factors}


def test_replication_strengthens_claim(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "replication": {"replication_arm_count": 4, "failed_replication_count": 0},
        "claims": [_claim({"direct_evidence": True, "replication_evidence": True,
                           "control_comparison": True})]})
    rt.run()
    claim = rt.registry.get("c1")
    assert claim.status == ClaimStatus.SUPPORTED
    assert claim.strength == "strong"


def test_falsification_weakens_or_blocks_claim(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "falsification": {"falsified_claim_count": 1},
        "claims": [_claim({"direct_evidence": True, "replication_evidence": True,
                           "falsified_core": True})]})
    rt.run()
    claim = rt.registry.get("c1")
    assert claim.status == ClaimStatus.FALSIFIED
    # Counterevidence records the falsification.
    assert rt.counterevidence["counterevidence_count"] >= 1
    assert rt.scientific_claims_status()["falsified_claim_count"] >= 1
