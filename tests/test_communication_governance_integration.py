"""Tests for governance over the communication layer."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.governance import GovernancePolicy, PermissionScope


def _manifest_view(features=None, **kw):
    return {"mode": "bounded", "max_steps": 100,
            "checkpoint_interval_steps": 50,
            "enabled_features": features or {}, **kw}


def test_communication_allowed_in_bounded_runs():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"communication": True}))
    assert decision.allowed
    assert policy.permissions.allows(
        PermissionScope.ENABLE_OPERATOR_DIALOGUE)


def test_state_query_allowed(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"governance": GovernancePolicy(),
                    "ops_status": {"health_level": "ok"}})
    response = gateway.handle_input("status")
    assert response.kind == "status"
    assert response.governance_status == "ok"


def test_report_generation_needs_claim_guard(tmp_path):
    """Reports flow through the ClaimGuard-scanned builders only."""
    from solaris_ai_nn.ego.self_model import SelfModel

    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"ego": ego, "governance": GovernancePolicy()})
    response = gateway.handle_input("generate self-report")
    assert response.kind == "report"
    assert "claim guard safe: True" in response.text
    # The policy names the requirement explicitly.
    rules = {r["rule_id"] for r in GovernancePolicy().to_dict()["rules"]
             if r["category"] == "communication"}
    assert "reports_require_claim_guard" in rules


def test_sensory_text_blocked_by_default(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"governance": GovernancePolicy()})
    response = gateway.handle_input("stimulus: bright light ahead")
    assert response.kind == "sensory_disabled"
    assert not response.executed
    assert "recorded, not injected" in response.text
    # The governance scope is approval-gated too.
    assert GovernancePolicy().permissions.requires_approval(
        PermissionScope.OPERATOR_SEND_SENSORY_TEXT)


def test_safe_shutdown_always_allowed(tmp_path):
    from solaris_ai_nn.ops.safe_shutdown import SafeShutdownManager

    policy = GovernancePolicy()
    policy.permissions.revoke(
        PermissionScope.OPERATOR_REQUEST_SAFE_SHUTDOWN)
    shutdown = SafeShutdownManager(ops_dir=tmp_path / "ops")
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"governance": policy, "shutdown": shutdown})
    response = gateway.handle_input("emergency stop")
    assert response.kind == "emergency"
    assert shutdown.requested  # scope revocation cannot block the stop


def test_raw_command_execution_named_in_policy():
    policy = GovernancePolicy()
    decision = policy.evaluate_manifest(
        _manifest_view({"communication": True}),
        context={"raw_command_execution": True})
    assert not decision.allowed
    assert any(v.rule_id == "no_raw_command_execution"
               for v in decision.violations)
