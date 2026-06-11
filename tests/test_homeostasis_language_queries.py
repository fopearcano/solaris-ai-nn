"""Tests for the homeostasis language queries."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.homeostasis.reports import HomeostasisQueryInterface


def _regulator():
    regulator = HomeostaticRegulator()
    regulator.update({
        "embodiment": {"energy": 0.8, "max_energy": 10.0,
                       "exhausted": True, "dist_reward": 1.0},
        "latent": {"mysterium_pressure": 0.8,
                   "anticipation_accuracy": 0.4},
    })
    return regulator


def test_dominant_need_query_grounded():
    queries = HomeostasisQueryInterface(_regulator())
    result = queries.answer("what is the dominant need?")
    assert result.answered
    assert "need estimator assigned" in result.text
    assert "derived from:" in result.text  # names its source variables


def test_desire_explanation_avoids_wanted_felt():
    queries = HomeostasisQueryInterface(_regulator())
    result = queries.answer("why was this desire suggested?")
    assert result.answered
    lowered = result.text.lower()
    assert "wanted" not in lowered and "felt" not in lowered \
        and "feels" not in lowered
    assert "suggested a Desire object" in result.text
    assert "nothing was executed" in result.text


def test_all_seven_queries_supported_and_safe():
    regulator = _regulator()
    regulator.update({"health_level": "critical",
                      "critical_incident": True})
    queries = HomeostasisQueryInterface(regulator)
    assert len(queries.supported_queries()) == 7
    guard = ClaimGuard()
    for question in queries.supported_queries():
        answer = queries.answer(question)
        assert guard.is_safe(answer.text), question
        assert "want" not in answer.text.lower().replace("unwanted", "")


def test_rest_and_shutdown_explanations():
    regulator = _regulator()
    queries = HomeostasisQueryInterface(regulator)
    rest = queries.answer("why did the system recommend rest?")
    assert "high pressure" in rest.text or "within range" in rest.text
    regulator.update({"health_level": "critical",
                      "critical_incident": True})
    shutdown = queries.answer(
        "why did the system recommend safe shutdown?")
    assert "recommendation only" in shutdown.text
    assert "ops supervisor/watchdog decides" in shutdown.text


def test_unknown_query_falls_back():
    queries = HomeostasisQueryInterface(_regulator())
    result = queries.answer("does the system love rewards?")
    assert not result.answered
    assert "does not know how to answer" in result.text
