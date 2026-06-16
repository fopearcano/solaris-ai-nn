"""Independent review <-> Operator Console + Inner MAP integration."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import (
    AVAILABLE_QUERIES,
    QueryRouter,
)
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.independent_review import IndependentReviewRuntime


def _runtime(tmp_path):
    rt = IndependentReviewRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3},
        "safety": {"critical_regression_count": 0},
        "scientific_claims": {
            "claim_registry": {"scientific_claim_count": 1,
                               "supported_claim_count": 1, "claims": [
                {"claim_id": "c1", "text": "Signs form.",
                 "category": "sensorium_claim", "status": "supported",
                 "evidence_refs": ["e1"], "counterevidence_refs": []}]},
            "counterevidence": {"counterevidence_count": 0, "records": []},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": []}},
        "sanitizer_inputs": {"abstract": "Signs form. It is not conscious."}})
    rt.run()
    return rt


def test_ready_question_safe_answer():
    cls = OperatorInputClassifier().classify("is this ready for external review?")
    assert cls.args.get("topic") == "ir_ready"
    resp = QueryRouter(components={}).route_query(cls)
    assert "inspectable" in resp.text


def test_publish_question_safe_answer():
    cls = OperatorInputClassifier().classify("did Solaris publish anything?")
    resp = QueryRouter(components={}).route_query(cls)
    assert "does not publish" in resp.text


def test_contact_question_safe_answer():
    cls = OperatorInputClassifier().classify("did Solaris contact reviewers?")
    resp = QueryRouter(components={}).route_query(cls)
    assert "does not contact reviewers" in resp.text


def test_operator_exposes_review_readiness(tmp_path):
    rt = _runtime(tmp_path)
    cls = OperatorInputClassifier().classify("what should a reviewer test?")
    resp = QueryRouter(components={"independent_review": rt}).route_query(cls)
    assert "reproducibility" in resp.text.lower()


def test_available_queries_listed():
    assert "is this ready for external review?" in AVAILABLE_QUERIES
    assert "did Solaris publish anything?" in AVAILABLE_QUERIES


def test_inner_map_includes_review_state(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(independent_review=rt).update()
    assert model.independent_review is not None
    assert model.independent_review["independent_review_enabled"] is True
    assert model.independent_review["published"] is False
    assert "independent_review" in model.to_dict()


def test_state_graph_has_review_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "ReviewArtifactSanitizer" in nodes
    assert "AdversarialReviewEngine" in nodes
    assert "IndependentReviewRuntime" in nodes
