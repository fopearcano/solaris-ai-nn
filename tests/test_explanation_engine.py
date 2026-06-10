"""Tests for the ExplanationEngine."""

from __future__ import annotations

from solaris_ai_nn.language.explanation import ExplanationEngine
from solaris_ai_nn.language.schemas import ExplanationContext

ENGINE = ExplanationEngine()


def _ctx(**kw) -> ExplanationContext:
    return ExplanationContext(**kw)


def test_explains_last_signal():
    ctx = _ctx(last_signal={"kind": "Stimulus", "origin": "world",
                            "intensity": 0.8})
    e = ENGINE.explain_last_event(ctx)
    assert "Stimulus" in e.text and "world" in e.text and "0.8" in e.text
    assert e.grounded_in  # references concrete fields


def test_explains_action_suggestion():
    ctx = _ctx(bridge={"last_suggested_action": "approach",
                       "last_confidence": 0.7, "substrate_type": "esn",
                       "substrate_state_norm": 4.0,
                       "substrate_config": {"state_size": 64},
                       "substrate_metrics": {"drift": 0.1}})
    e = ENGINE.explain_action_suggestion(ctx)
    assert "suggested approach" in e.text
    assert "tendency, not a committed decision" in e.text


def test_explains_blocked_action():
    ctx = _ctx(last_result={"action": "move_north", "executed": False,
                            "blocked_reason": "wall"})
    e = ENGINE.explain_blocked_action(ctx)
    assert "blocked because wall" in e.text
    # Executed action: reports it was NOT blocked.
    ctx2 = _ctx(last_result={"action": "rest", "executed": True,
                             "consequence": "recovered"})
    assert "was not blocked" in ENGINE.explain_blocked_action(ctx2).text


def test_explains_unknown_gracefully():
    empty = _ctx()
    for method in (ENGINE.explain_last_event, ENGINE.explain_action_suggestion,
                   ENGINE.explain_strongest_habit, ENGINE.explain_embodiment,
                   ENGINE.explain_plasticity, ENGINE.explain_inner_map):
        e = method(empty)
        assert "does not know" in e.text
        assert e.confidence == 0.0
        assert e.unknowns  # names what is missing


def test_no_motivational_language():
    ctx = _ctx(bridge={"last_suggested_action": "approach",
                       "last_confidence": 0.5, "substrate_type": "esn",
                       "substrate_config": {}, "substrate_metrics": {}})
    text = ENGINE.explain_action_suggestion(ctx).text
    assert "I wanted" not in text
    assert "wants" not in text
