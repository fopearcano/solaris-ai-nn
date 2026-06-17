"""First tester integration: membrane/raw-event stops, claims blocked, alpha status."""

from __future__ import annotations

from _first_tester_helpers import run_protocol

from solaris_ai_nn.alpha_system.alpha_orchestrator import (
    AlphaResearchOrchestrator,
)
from solaris_ai_nn.first_tester_protocol import (
    FirstTesterProtocolSafetyValidator,
    FirstTesterStopConditions,
)


def test_membrane_bypass_stop_condition_present():
    text = FirstTesterStopConditions().build_text().lower()
    assert "membrane is missing" in text


def test_raw_event_bypass_stop_condition_present():
    text = FirstTesterStopConditions().build_text().lower()
    assert "raw-event bypass" in text


def test_unsupported_claims_blocked():
    v = FirstTesterProtocolSafetyValidator()
    assert not v.validate_claim_text("Solaris is conscious and alive").safe


def test_alpha_exposes_protocol_status(tmp_path):
    base = str(tmp_path / "p")
    run_protocol(base)
    st = AlphaResearchOrchestrator().first_tester_protocol_status(base)
    assert st["first_tester_protocol_available"] is True
    assert st["runs_session"] is False
    assert st["published"] is False


def test_alpha_protocol_absent(tmp_path):
    st = AlphaResearchOrchestrator().first_tester_protocol_status(
        str(tmp_path / "nope"))
    assert st["first_tester_protocol_available"] is False
