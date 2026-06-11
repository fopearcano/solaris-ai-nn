"""Tests for the query router."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    OperatorInputClassifier,
)
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.governance.approval import ApprovalRegistry


def _route(router, text):
    return router.route_query(OperatorInputClassifier().classify(text))


def test_routes_status_query():
    router = QueryRouter(components={
        "ops_status": {"steps": 42, "health_level": "ok"}})
    response = _route(router, "status")
    assert response.kind == "status"
    assert "steps=42" in response.text
    assert "field:steps" in response.evidence_refs


def test_routes_boundary_query(tmp_path):
    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    router = QueryRouter(components={"ego": ego})
    response = _route(router, "show boundaries")
    assert "boundary_count=16" in response.text
    assert response.grounded


def test_routes_pending_approvals_query():
    registry = ApprovalRegistry()
    request = registry.request_approval("enable_latent_plasticity",
                                        reason="test")
    router = QueryRouter(components={"approvals": registry})
    response = _route(router, "what approvals are pending?")
    assert request.request_id in response.text
    assert f"approval:{request.request_id}" in response.evidence_refs
    # And with nothing pending, it says so.
    registry.reject(request.request_id, "op", reason="done")
    empty = _route(router, "what approvals are pending?")
    assert "no approval requests are pending" in empty.text


def test_unsupported_query_returns_safe_fallback():
    router = QueryRouter(components={})
    response = _route(router, "show world model")
    assert response.kind == "missing_component"
    assert "not attached" in response.text
    assert router.unknown_answers == 1


def test_explanation_falls_back_to_no_evidence():
    router = QueryRouter(components={})
    response = _route(router, "why did the universe begin?")
    assert response.text == "The system has no evidence for that answer."


def test_evidence_support_query_reflects_last_answer():
    router = QueryRouter(components={
        "ops_status": {"steps": 7, "health_level": "ok"}})
    _route(router, "status")
    response = _route(router, "what evidence supports this answer?")
    assert "grounded in" in response.text
    assert "field:steps" in response.text


def test_available_queries_and_snapshot():
    router = QueryRouter(components={"ops_status": {}})
    queries = router.available_queries()
    assert "what can I ask?" in queries
    assert "status" in queries
    snapshot = router.snapshot()
    assert snapshot["components_attached"] == ["ops_status"]
