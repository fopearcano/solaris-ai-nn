"""Tests for the communication meta-queries."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.governance.policy import GovernancePolicy


def _gateway(tmp_path):
    return CommunicationGateway(
        state_dir=tmp_path,
        components={"governance": GovernancePolicy(),
                    "ops_status": {"health_level": "ok"}})


def test_allowed_commands_query_works(tmp_path):
    gateway = _gateway(tmp_path)
    response = gateway.handle_input("what commands are allowed?")
    assert "allowed command types" in response.text
    assert "show_status" in response.text
    assert "request_safe_shutdown" in response.text


def test_forbidden_commands_query_works(tmp_path):
    gateway = _gateway(tmp_path)
    response = gateway.handle_input("what commands are forbidden?")
    assert "forbidden command types" in response.text
    assert "execute_shell" in response.text
    assert "do not exist here" in response.text


def test_what_can_i_ask_query(tmp_path):
    gateway = _gateway(tmp_path)
    response = gateway.handle_input("what can I ask?")
    assert "supported queries" in response.text
    assert "why no action?" in response.text


def test_transcript_summary_query(tmp_path):
    gateway = _gateway(tmp_path)
    gateway.handle_input("status")
    response = gateway.handle_input("show transcript summary")
    assert "entries_in_memory" in response.text
    assert response.grounded


def test_evidence_support_query_works(tmp_path):
    gateway = _gateway(tmp_path)
    gateway.handle_input("status")
    response = gateway.handle_input(
        "what evidence supports this answer?")
    assert "grounded in" in response.text
    assert "field:" in response.text


def test_meta_answers_claim_safe_and_grounded(tmp_path):
    gateway = _gateway(tmp_path)
    guard = ClaimGuard()
    for text in ("what can I ask?", "what commands are allowed?",
                 "what commands are forbidden?",
                 "what approvals are pending?",
                 "show transcript summary"):
        response = gateway.handle_input(text)
        assert guard.is_safe(response.text), text
        assert response.grounded, text
        lowered = response.text.lower()
        for forbidden in ("i want", "i feel", "i am conscious"):
            assert forbidden not in lowered
