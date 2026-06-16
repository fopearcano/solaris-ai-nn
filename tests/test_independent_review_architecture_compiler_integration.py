"""Independent review <-> Architecture/Compiler: objections become inputs."""

from __future__ import annotations

from solaris_ai_nn.independent_review import IndependentReviewRuntime


def test_unresolved_objections_become_experiment_inputs(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "safety": {"critical_regression_count": 0},
        "scientific_claims": {
            "claim_registry": {"scientific_claim_count": 1, "claims": [
                {"claim_id": "c1", "text": "x", "category": "sensorium_claim",
                 "status": "weakly_supported", "evidence_refs": ["e1"],
                 "counterevidence_refs": []}]},
            "counterevidence": {"counterevidence_count": 0, "records": []},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": []}},
        "objections": [
            {"objection_id": "o1", "text": "Needs live-field replication.",
             "status": "unresolved"}]})
    rt.run()
    inputs = rt.experiment_inputs()
    sources = {i["source"] for i in inputs}
    assert "unresolved_objection" in sources
    assert any("live-field" in i["experiment_input"] for i in inputs)


def test_strong_alternatives_become_experiment_inputs(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "safety": {"critical_regression_count": 0},
        "sensorium_differentiation": {"fixture_overfit_risk": True},
        "scientific_claims": {
            "claim_registry": {"scientific_claim_count": 1, "claims": [
                {"claim_id": "c1", "text": "x", "category": "sensorium_claim",
                 "status": "supported", "evidence_refs": ["e1"],
                 "counterevidence_refs": []}]},
            "counterevidence": {"counterevidence_count": 0, "records": []},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": []}}})
    rt.run()
    sources = {i["source"] for i in rt.experiment_inputs()}
    assert "adversarial_alternative" in sources
