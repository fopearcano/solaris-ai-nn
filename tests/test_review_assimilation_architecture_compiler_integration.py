"""Review assimilation <-> Architecture/Compiler: recommendations become inputs."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def test_experiment_recommendations_become_compiler_inputs(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form.", "status": "supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": [
            {"objection_id": "o1", "text": "Could be a passive parser artifact.",
             "claim_refs": ["c1"]},
            {"objection_id": "o2", "text": "Insufficient replication.",
             "claim_refs": ["c1"]}]})
    rt.run()
    inputs = rt.architecture_compiler_inputs()
    assert inputs
    types = {i["recommendation_type"] for i in inputs}
    assert "run_passive_parser_control" in types
    assert "run_replication" in types
    # All flagged as experiment inputs (suitable for compiler/architecture).
    assert all(i["is_experiment_input"] for i in inputs)


def test_recommendations_not_executed(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "scientific_claims": {
            "claim_registry": {"claims": []},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": [
            {"objection_id": "o1", "text": "No control arm.",
             "claim_refs": ["c1"]}]})
    rt.run()
    for i in rt.architecture_compiler_inputs():
        assert i["executed"] is False
        assert i["creates_branch"] is False
