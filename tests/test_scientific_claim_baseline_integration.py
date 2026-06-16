"""Scientific claims <-> Research Baseline: capability/limitation/safety bounds."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def _claim():
    return {"claim_id": "c1", "text": "Architecture forms stable signs.",
            "category": "baseline_claim",
            "evidence": [{"evidence_id": "cap_map", "source": "research_baseline",
                          "role": "supports"}],
            "factors": {"direct_evidence": True, "replication_evidence": True,
                        "control_comparison": True, "safety_preserved": True}}


def test_consumes_capability_map(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass",
                              "capability_count": 5},
        "replication": {"replication_arm_count": 3},
        "claims": [_claim()]})
    rt.run()
    assert "cap_map" in rt.evidence_map.supporting_refs("c1")
    assert rt.scientific_claims_status()["supported_claim_count"] == 1


def test_limitation_registry_consumed(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated"},
        "fixture_overfit_risk": True, "missing_live_data": True,
        "claims": [_claim()]})
    rt.run()
    cats = {l["category"] for l in rt.limitations["limitations"]}
    assert "fixture_dependence" in cats
    assert "missing_live_data" in cats


def test_safety_boundary_constrains_claims(tmp_path):
    rt = ScientificClaimRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "blocked",
                              "safety_boundary_status": "boundary_failed"},
        "claims": [_claim()]})
    rt.run()
    # A failed safety boundary blocks the publishable claim.
    st = rt.scientific_claims_status()
    assert st["supported_claim_count"] == 0
    assert st["publication_readiness_status"] == "blocked_by_safety"
