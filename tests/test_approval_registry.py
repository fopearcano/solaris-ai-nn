"""Tests for the ApprovalRegistry."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.governance.approval import (
    APPROVED,
    EXPIRED,
    PENDING,
    REJECTED,
    ApprovalRegistry,
)


def test_approval_request_created(tmp_path):
    registry = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = registry.request_approval(
        "enable_plasticity_apply", reason="experiment 12",
        risk_level="high", operator_name="alice")
    assert request.status == PENDING
    assert request.requested_permission == "enable_plasticity_apply"
    assert request.request_id
    assert registry.list_pending() == [request]
    assert not registry.is_approved("enable_plasticity_apply")


def test_approval_granted(tmp_path):
    registry = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = registry.request_approval("run_soak_24h", reason="soak pilot")
    registry.approve(request.request_id, "alice", note="checklist complete")
    assert request.status == APPROVED
    assert request.decided_by == "alice"
    assert registry.is_approved("run_soak_24h")
    assert registry.records[-1].action == "approved"


def test_approval_rejected(tmp_path):
    registry = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = registry.request_approval("run_soak_30d", reason="too early")
    registry.reject(request.request_id, "bob", reason="no restart test yet")
    assert request.status == REJECTED
    assert not registry.is_approved("run_soak_30d")
    with pytest.raises(ValueError):  # cannot re-decide
        registry.approve(request.request_id, "alice")


def test_expired_approval_not_valid(tmp_path):
    registry = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = registry.request_approval(
        "enable_sidecar_suggestions", expires_in_s=0.01)
    registry.approve(request.request_id, "alice")
    assert registry.is_approved("enable_sidecar_suggestions")
    time.sleep(0.05)
    assert not registry.is_approved("enable_sidecar_suggestions")
    assert request.status == EXPIRED
    assert registry.expired_count() == 1


def test_required_confirmations(tmp_path):
    registry = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = registry.request_approval("run_soak_24h",
                                        required_confirmations=2)
    registry.approve(request.request_id, "alice")
    assert request.status == PENDING  # one confirmation is not enough
    registry.approve(request.request_id, "bob")
    assert request.status == APPROVED


def test_run_pinned_approval(tmp_path):
    registry = ApprovalRegistry(path=tmp_path / "approvals.json")
    request = registry.request_approval("enable_plasticity_apply",
                                        run_id="run-A")
    registry.approve(request.request_id, "alice")
    assert registry.is_approved("enable_plasticity_apply",
                                {"run_id": "run-A"})
    assert not registry.is_approved("enable_plasticity_apply",
                                    {"run_id": "run-B"})


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "approvals.json"
    registry = ApprovalRegistry(path=path)
    request = registry.request_approval("run_soak_24h", reason="pilot")
    registry.approve(request.request_id, "alice")
    registry.save()

    reloaded = ApprovalRegistry(path=path)  # loads in __post_init__
    assert reloaded.is_approved("run_soak_24h")
    assert len(reloaded.records) == 1


def test_audit_rows_written(tmp_path):
    from solaris_ai_nn.governance.audit import GovernanceAuditLog

    audit = GovernanceAuditLog(tmp_path / "audit.jsonl")
    registry = ApprovalRegistry(path=tmp_path / "approvals.json", audit=audit)
    request = registry.request_approval("run_soak_24h")
    registry.approve(request.request_id, "alice")
    request2 = registry.request_approval("run_soak_30d")
    registry.reject(request2.request_id, "alice", "not yet")
    types = [r["event_type"] for r in audit.read_all()]
    assert types == ["approval_requested", "approval_granted",
                     "approval_requested", "approval_rejected"]
