"""Tests for communication state inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_inner_map_includes_communication_state(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"governance": GovernancePolicy(),
                    "ops_status": {"health_level": "ok"}})
    gateway.handle_input("status")
    gateway.handle_input("sudo rm -rf /")
    model = InnerMapObserver(communication=gateway).update()
    assert model.communication is not None
    for key in ("enabled", "dialogue_mode", "last_input_kind",
                "unsafe_request_count", "pending_confirmation_count",
                "pending_approval_count", "transcript_path",
                "last_response_summary", "operator_session_id",
                "safety_status"):
        assert key in model.communication, key
    assert model.communication["unsafe_request_count"] == 1
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.communication["enabled"] is True


def test_communication_absent_when_disabled():
    assert InnerMapObserver().update().communication is None


def test_state_graph_includes_communication_nodes():
    graph = build_default_state_graph()
    for node in ("communication_gateway", "operator_input_classifier",
                 "command_router", "communication_query_router",
                 "approval_router", "response_builder",
                 "communication_transcript",
                 "communication_safety_validator"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("communication_gateway",
            "operator_input_classifier") in edges
    assert ("operator_input_classifier",
            "communication_safety_validator") in edges
    assert ("communication_query_router", "inner_map") in edges
    assert ("command_router", "action_arbitrator") in edges
    assert ("response_builder", "communication_gateway") in edges
    assert ("communication_transcript", "inner_map") in edges
    assert "communication_gateway" in graph.to_mermaid()
