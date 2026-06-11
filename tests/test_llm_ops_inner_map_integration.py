"""Tests for LLM status in ops and the Inner MAP."""

from __future__ import annotations

import inspect

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def _gateway(tmp_path, **kw):
    return CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components={"ops_status": {"steps": 3, "health_level": "ok"}},
        **kw)


def test_ops_status_includes_llm_status(tmp_path):
    gateway = _gateway(tmp_path)
    gateway.handle_input("status")
    summary = gateway.summary()
    for key in ("llm_adapter_enabled", "llm_provider",
                "llm_last_task_type", "llm_fallback_count",
                "llm_grounding_failure_count",
                "llm_claim_guard_warning_count",
                "llm_last_grounding_status", "llm_authority"):
        assert key in summary, key
    assert summary["llm_provider"] == "mock"
    assert summary["llm_last_task_type"] == "paraphrase_response"
    # The supervisor picks the whole summary up via runner.communication.
    source = inspect.getsource(OperationalSupervisor._health_snapshot)
    assert 'getattr(runner, "communication", None)' in source


def test_inner_map_includes_llm_audit_path(tmp_path):
    gateway = _gateway(tmp_path)
    gateway.handle_input("status")
    model = InnerMapObserver(communication=gateway).update()
    assert model.communication is not None
    assert model.communication["llm_adapter_enabled"] is True
    assert model.communication["llm_audit_path"].endswith(
        "llm_audit.jsonl")
    assert model.communication["llm_authority"] is False


def test_grounding_failures_create_warning(tmp_path):
    gateway = _gateway(tmp_path,
                       llm_adapter=MockLLMAdapter(
                           force_unsafe_output=True))
    for _ in range(3):
        gateway.handle_input("status")
    summary = gateway.summary()
    assert summary["llm_grounding_failure_count"] >= 3
    # The supervisor monitoring block converts this into an incident.
    source = inspect.getsource(OperationalSupervisor._supervise)
    block = source.split("LLM adapter monitoring")[1].split(
        "Ego/self-model monitoring")[0]
    assert "llm_grounding_failure_count" in block
    assert "request_shutdown" not in block  # evidence only


def test_state_graph_includes_llm_nodes():
    graph = build_default_state_graph()
    for node in ("llm_adapter", "local_http_llm_adapter",
                 "mock_llm_adapter", "grounding_validator",
                 "llm_paraphraser", "llm_classification_assistant",
                 "llm_summarizer", "report_polisher", "llm_audit_log"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("response_builder", "llm_paraphraser") in edges
    assert ("llm_adapter", "grounding_validator") in edges
    assert ("llm_paraphraser", "communication_gateway") in edges
    assert ("llm_audit_log", "inner_map") in edges
    # The LLM never feeds executive authority: no edge into the
    # arbitrator from any llm node.
    llm_nodes = {n for n in graph.nodes if "llm" in n}
    assert not any(src in llm_nodes and dst == "action_arbitrator"
                   for src, dst, _ in graph.edges)
