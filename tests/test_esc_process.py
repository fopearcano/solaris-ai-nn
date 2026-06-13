"""Tests for the Esc process."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.esc_process import EscProcess, EscResponse


def test_unresolved_high_severity_triggers_esc():
    esc = EscProcess()
    state = esc.evaluate({"unresolved_high_severity_count": 3,
                          "complexity": {"band": "overloaded"}})
    assert state.triggered is True


def test_esc_requests_stabilization():
    esc = EscProcess()
    state = esc.evaluate({"unresolved_high_severity_count": 3,
                          "mysterium_pressure": 0.96})
    assert EscResponse.REQUEST_STABILIZATION in state.responses


def test_esc_cannot_execute_action():
    # Structural: every Esc response is a *request*, never an execution.
    esc = EscProcess()
    state = esc.evaluate({"unresolved_high_severity_count": 3,
                          "mysterium_pressure": 0.96})
    assert all(r in EscResponse.ALL for r in state.responses)
    assert all(r.startswith("request_") or r.startswith("mark_")
               for r in state.responses)


def test_calm_context_no_trigger():
    esc = EscProcess()
    assert esc.evaluate({"mysterium_pressure": 0.2}).triggered is False


def test_mysterium_saturation_marks_unresolved():
    esc = EscProcess()
    state = esc.evaluate({"mysterium_pressure": 0.96,
                          "unresolved_high_severity_count": 1})
    assert EscResponse.MARK_UNRESOLVED_MYSTERIUM in state.responses
