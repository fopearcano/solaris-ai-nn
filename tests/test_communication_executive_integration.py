"""Tests for operator requests flowing into executive arbitration."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.governance.policy import GovernancePolicy


def _gateway(tmp_path):
    executive = ExecutiveLayer()
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"executive": executive,
                    "governance": GovernancePolicy()})
    return gateway, executive


def test_checkpoint_request_becomes_safe_internal_candidate(tmp_path):
    gateway, executive = _gateway(tmp_path)
    response = gateway.handle_input("run a checkpoint")
    assert response.kind == "confirmation_request"
    confirmation_id = response.suggested_next_operator_action.split()[-1]
    confirmed = gateway.handle_input(f"confirm {confirmation_id}")
    assert confirmed.kind == "request_recorded"
    # The request landed in the executive's desire queue as a candidate.
    proposals = [item.proposal for item in executive.queue.items]
    assert "checkpoint_now" in proposals
    queued = [item for item in executive.queue.items
              if item.proposal == "checkpoint_now"][0]
    assert queued.candidate.metadata["source"] == "operator_request"
    # The executive still arbitrates; the gateway committed nothing.
    result = executive.decide([], context={}, step=1)
    assert result.selected.committed is False


def test_unsafe_command_never_reaches_executive(tmp_path):
    gateway, executive = _gateway(tmp_path)
    gateway.handle_input("execute shell rm -rf /")
    gateway.handle_input("move the robot arm")
    assert len(executive.queue) == 0
    assert executive.decisions == 0


def test_gateway_cannot_commit_external_actions(tmp_path):
    import inspect

    from solaris_ai_nn.communication import command_router

    source = inspect.getsource(command_router)
    assert "committed=True" not in source
    gateway, executive = _gateway(tmp_path)
    response = gateway.handle_input("emergency stop")
    # Even the emergency path records requests; it commits no Action.
    assert "Safe shutdown status" in response.text
