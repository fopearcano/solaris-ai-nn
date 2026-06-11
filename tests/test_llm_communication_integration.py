"""Tests for the LLM adapter inside the communication gateway."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter

COMPONENTS = {"ops_status": {"steps": 9, "health_level": "ok"}}


def test_gateway_works_with_llm_disabled(tmp_path):
    gateway = CommunicationGateway(state_dir=tmp_path,
                                   components=dict(COMPONENTS))
    assert gateway.llm_paraphraser is None
    response = gateway.handle_input("status")
    assert response.kind == "status"
    assert not response.metadata.get("llm_paraphrased")
    assert gateway.summary()["llm_adapter_enabled"] is False
    assert gateway.summary()["llm_authority"] is False


def test_gateway_works_with_mock_llm_enabled(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components={**COMPONENTS, "governance": GovernancePolicy()})
    response = gateway.handle_input("status")
    assert response.metadata.get("llm_paraphrased") is True
    assert response.text.startswith("In plain terms:")
    assert "steps=9" in response.text  # facts preserved
    summary = gateway.summary()
    assert summary["llm_adapter_enabled"] is True
    assert summary["llm_provider"] == "mock"
    assert summary["llm_authority"] is False
    assert summary["llm_audit_path"].endswith("llm_audit.jsonl")


def test_deterministic_safety_still_controls_output(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        llm_adapter=MockLLMAdapter(force_unsafe_output=True),
        components=dict(COMPONENTS))
    response = gateway.handle_input("status")
    # The unsafe paraphrase was rejected; the deterministic text stands.
    assert not response.metadata.get("llm_paraphrased")
    assert response.text.startswith("Status summary:")
    assert gateway.llm_paraphraser.rejected_count == 1
    assert gateway.summary()["llm_fallback_count"] == 1


def test_unsafe_request_refused_regardless_of_llm(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components=dict(COMPONENTS))
    response = gateway.handle_input("sudo rm -rf /")
    assert response.kind == "unsafe_refusal"
    # Refusals are never paraphrased.
    assert not response.metadata.get("llm_paraphrased")


def test_refusals_and_emergency_never_paraphrased(tmp_path):
    from solaris_ai_nn.ops.safe_shutdown import SafeShutdownManager

    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components={**COMPONENTS,
                    "shutdown": SafeShutdownManager(
                        ops_dir=tmp_path / "ops")})
    emergency = gateway.handle_input("emergency stop")
    assert emergency.kind == "emergency"
    assert not emergency.metadata.get("llm_paraphrased")
    assert emergency.text.startswith("Emergency stop was requested")


def test_assist_upgrades_unknown_to_query_only(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path, enable_llm_adapter=True,
        components=dict(COMPONENTS))
    response = gateway.handle_input(
        "err hmm what about the status maybe")
    assert response.kind == "status"  # read-only upgrade
    # But approval-shaped ambiguity never becomes an approval command.
    odd = gateway.handle_input("hmm maybe approve-ish something blorp")
    assert odd.kind in ("unknown", "status")
    assert odd.kind != "governance"
