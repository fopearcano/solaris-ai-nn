"""Tests for the executive language queries."""

from __future__ import annotations

from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.executive.reports import ExecutiveQueryInterface
from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def _layer(context=None):
    layer = ExecutiveLayer()
    layer.decide([DesireCandidate(proposal="rest", motivation=0.7,
                                  confidence=0.7),
                  DesireCandidate(proposal="explore_safely",
                                  motivation=0.4, confidence=0.5)],
                 context=context or {}, step=1)
    return layer


def test_why_selected_uses_safe_vocabulary():
    queries = ExecutiveQueryInterface(_layer())
    result = queries.answer("why was this action selected?")
    assert result.answered
    assert "The arbitrator selected" in result.text
    assert "suggestion" in result.text
    lowered = result.text.lower()
    assert "decided freely" not in lowered
    assert "wanted" not in lowered and "chose to" not in lowered


def test_rejected_and_inhibited_queries_grounded():
    layer = _layer(context={"governance_blocks":
                            {"explore_safely": "operator pause"}})
    queries = ExecutiveQueryInterface(layer)
    rejected = queries.answer("what candidates were rejected?")
    assert rejected.answered
    inhibited = queries.answer("what was inhibited?")
    assert inhibited.answered
    assert "governance" in inhibited.text


def test_all_seven_queries_supported_and_claim_safe():
    queries = ExecutiveQueryInterface(_layer())
    assert len(queries.supported_queries()) == 7
    guard = ClaimGuard()
    for question in queries.supported_queries():
        answer = queries.answer(question)
        assert guard.is_safe(answer.text), question


def test_no_action_explained_as_valid_outcome():
    layer = ExecutiveLayer()
    layer.decide([], context={"observe_only": True}, step=1)
    queries = ExecutiveQueryInterface(layer)
    result = queries.answer("why no action?")
    if layer.last_result.selected.label == "no_action":
        assert "valid, safe outcome" in result.text


def test_winning_score_names_components():
    queries = ExecutiveQueryInterface(_layer())
    result = queries.answer("what score won arbitration?")
    assert result.answered
    assert "fourteen components" in result.text
    assert "decision" in result.text and "trace" in result.text


def test_unknown_query_falls_back():
    queries = ExecutiveQueryInterface(_layer())
    result = queries.answer("does the executive have free will?")
    assert not result.answered
    assert "does not know how to answer" in result.text
