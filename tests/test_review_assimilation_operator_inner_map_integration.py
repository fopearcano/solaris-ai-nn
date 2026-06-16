"""Review assimilation <-> Operator Console + Inner MAP integration."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import (
    AVAILABLE_QUERIES,
    QueryRouter,
)
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def _runtime(tmp_path):
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form.", "status": "supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": [
            {"objection_id": "o1", "text": "Probably fixture overfit.",
             "claim_refs": ["c1"]}]})
    rt.run()
    return rt


def test_train_question_safe_answer():
    cls = OperatorInputClassifier().classify(
        "did reviewer feedback train the model?")
    assert cls.args.get("topic") == "ra_train"
    resp = QueryRouter(components={}).route_query(cls)
    assert "not used as Human Feedback" in resp.text or \
        "not used as" in resp.text


def test_publish_question_safe_answer():
    cls = OperatorInputClassifier().classify("can we publish after this review?")
    resp = QueryRouter(components={}).route_query(cls)
    assert "does not publish automatically" in resp.text


def test_operator_exposes_objections(tmp_path):
    rt = _runtime(tmp_path)
    cls = OperatorInputClassifier().classify("what did reviewers object to?")
    resp = QueryRouter(
        components={"review_assimilation": rt}).route_query(cls)
    assert "objection" in resp.text.lower()


def test_operator_exposes_recommendations(tmp_path):
    rt = _runtime(tmp_path)
    cls = OperatorInputClassifier().classify(
        "what experiments should we run because of the review?")
    resp = QueryRouter(
        components={"review_assimilation": rt}).route_query(cls)
    assert "recommendation" in resp.text.lower() or "experiment" in resp.text.lower()


def test_available_queries_listed():
    assert "did reviewer feedback train the model?" in AVAILABLE_QUERIES
    assert "what did reviewers object to?" in AVAILABLE_QUERIES


def test_inner_map_includes_assimilation_state(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(review_assimilation=rt).update()
    assert model.review_assimilation is not None
    assert model.review_assimilation["review_assimilation_enabled"] is True
    assert model.review_assimilation["trains_model"] is False
    assert "review_assimilation" in model.to_dict()


def test_state_graph_has_assimilation_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "ReviewerObjectionClassification" in nodes
    assert "ClaimRevisionProposal" in nodes
    assert "ReviewerFeedbackAssimilationRuntime" in nodes
