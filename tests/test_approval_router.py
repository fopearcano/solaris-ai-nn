"""Tests for the approval router."""

from __future__ import annotations

import time

from solaris_ai_nn.communication.approval_router import ApprovalRouter
from solaris_ai_nn.communication.operator_commands import (
    CommandType,
    OperatorCommand,
)
from solaris_ai_nn.governance.approval import ApprovalRegistry


def _command(command_type, request_id, operator="op-1"):
    return OperatorCommand(type=command_type, operator=operator,
                           parsed_args={"request_id": request_id})


def test_approves_real_pending_request():
    registry = ApprovalRegistry()
    request = registry.request_approval("enable_sidecar_suggestions",
                                        reason="test")
    router = ApprovalRouter(registry=registry)
    response = router.handle(_command(
        CommandType.APPROVE_GOVERNANCE_REQUEST, request.request_id))
    assert "Approval recorded" in response.text
    assert registry.requests[request.request_id].status == "approved"
    assert router.approvals_processed == 1
    assert f"approval_request:{request.request_id}" \
        in response.evidence_refs


def test_rejects_real_pending_request():
    registry = ApprovalRegistry()
    request = registry.request_approval("enable_plasticity_apply",
                                        reason="test")
    router = ApprovalRouter(registry=registry)
    response = router.handle(_command(
        CommandType.REJECT_GOVERNANCE_REQUEST, request.request_id))
    assert "Rejection recorded" in response.text
    assert registry.requests[request.request_id].status == "rejected"
    assert router.rejections_processed == 1


def test_refuses_unknown_request():
    registry = ApprovalRegistry()
    router = ApprovalRouter(registry=registry)
    response = router.handle(_command(
        CommandType.APPROVE_GOVERNANCE_REQUEST, "nonexistent00"))
    assert "No pending approval request" in response.text
    assert not response.executed
    assert router.refused == 1


def test_refuses_expired_request():
    registry = ApprovalRegistry()
    request = registry.request_approval("run_soak_24h", reason="test",
                                        expires_in_s=0.01)
    time.sleep(0.05)
    router = ApprovalRouter(registry=registry)
    response = router.handle(_command(
        CommandType.APPROVE_GOVERNANCE_REQUEST, request.request_id))
    assert "cannot be decided" in response.text
    assert registry.requests[request.request_id].status == "expired"
    assert router.refused == 1


def test_approval_does_not_bypass_prohibitions():
    """An approval grants the named permission; forbidden actions stay
    forbidden regardless of any approval."""
    from solaris_ai_nn.communication.safety import (
        CommunicationSafetyValidator,
    )

    registry = ApprovalRegistry()
    request = registry.request_approval("enable_sidecar_suggestions",
                                        reason="test")
    ApprovalRouter(registry=registry).handle(_command(
        CommandType.APPROVE_GOVERNANCE_REQUEST, request.request_id))
    report = CommunicationSafetyValidator().validate_command(
        OperatorCommand(type="commit_sidecar_action"))
    assert not report.safe  # approved or not, the type does not exist
