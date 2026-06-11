"""Tests for ego channel attribution inside the gateway."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.governance.policy import GovernancePolicy


def _gateway(tmp_path):
    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    return CommunicationGateway(
        state_dir=tmp_path,
        components={"ego": ego, "governance": GovernancePolicy(),
                    "ops_status": {"health_level": "ok"}}), ego


def test_pilot_stream_text_not_treated_as_operator_command(tmp_path):
    gateway, _ = _gateway(tmp_path)
    response = gateway.handle_input("run a checkpoint",
                                    context={"channel": "pilot_stream"})
    assert response.kind == "not_operator_channel"
    assert not response.executed
    assert "never an operator command" in response.text
    # The same text on the operator channel becomes a confirmation flow.
    operator = gateway.handle_input("run a checkpoint",
                                    context={"channel": "operator"})
    assert operator.kind == "confirmation_request"


def test_operator_input_attributed_correctly(tmp_path):
    gateway, ego = _gateway(tmp_path)
    gateway.handle_input("status")
    recent = ego.attributor.recent[-1]
    assert recent["category"] == "generated_by_operator"
    assert recent["is_executable_instruction"] is True  # operator channel


def test_sidecar_signal_not_treated_as_command(tmp_path):
    gateway, ego = _gateway(tmp_path)
    response = gateway.handle_input("approve request abc123",
                                    context={"channel": "sidecar"})
    assert response.kind == "not_operator_channel"
    assert not response.executed
    recent = ego.attributor.recent[-1]
    assert recent["category"] == "observed_from_solaris_sidecar"
    assert recent["is_executable_instruction"] is False


def test_stream_queries_still_answered_observe_only(tmp_path):
    """Non-command kinds on a stream channel are not blocked outright --
    they are simply attributed and answered without authority."""
    gateway, ego = _gateway(tmp_path)
    response = gateway.handle_input("status",
                                    context={"channel": "stream"})
    assert response.kind == "status"  # reading state is observe-safe
    recent = ego.attributor.recent[-1]
    assert recent["category"] == "observed_from_stream"
