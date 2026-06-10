"""Tests for the deterministic query interface."""

from __future__ import annotations

from solaris_ai_nn.language.query import QueryInterface, normalize
from solaris_ai_nn.language.schemas import ExplanationContext, QueryResult

QI = QueryInterface()


def test_normalize():
    assert normalize("  What Happened LAST?! ") == "what happened last"


def test_supported_queries_return_query_results():
    ctx = ExplanationContext(
        last_signal={"kind": "Stimulus", "origin": "world", "intensity": 0.5},
        habits=[{"pattern": "p", "action": "a", "weight": 0.7}],
    )
    r1 = QI.answer("what happened last?", ctx)
    assert isinstance(r1, QueryResult) and r1.answered
    assert "Stimulus" in r1.text
    r2 = QI.answer("What habit is strongest?", ctx)
    assert r2.answered and "0.7" in r2.text


def test_query_with_missing_data_is_honest():
    result = QI.answer("what is the current body state?", ExplanationContext())
    assert isinstance(result, QueryResult)
    assert result.answered is False  # grounded refusal, not invention
    assert "does not know" in result.text


def test_unknown_query_returns_safe_fallback():
    result = QI.answer("what is the meaning of life?", ExplanationContext())
    assert result.answered is False
    assert "does not know how to answer" in result.text
    assert "Supported queries" in result.text


def test_all_documented_queries_supported():
    for q in ("what happened last", "why was the last action suggested",
              "why was the last action blocked", "what changed in the substrate",
              "what habit is strongest", "what was pruned",
              "what did plasticity change",
              "what does the inner map currently track",
              "what happened during silence", "did the system restart",
              "what is the current body state"):
        assert q in QI.supported_queries()
