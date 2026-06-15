"""ConsequenceTrace: before/after recorded; ambiguous preserved; not invented."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import ConsequenceTrace, ConsequenceType
from solaris_ai_nn.action_reaction.consequence import (
    ConsequenceWindow,
    consequence_type_for_reaction,
)


def test_before_after_state_recorded():
    trace = ConsequenceTrace(
        consequence_type=ConsequenceType.IMMEDIATE_INTERNAL_CHANGE,
        action_refs=["A1"], reaction_refs=["R1"],
        before_state_summary={"uncertainty": 0.6},
        after_state_summary={"uncertainty": 0.4},
        window=ConsequenceWindow(start_tick=0, end_tick=3))
    d = trace.to_dict()
    assert d["before_state_summary"]["uncertainty"] == 0.6
    assert d["after_state_summary"]["uncertainty"] == 0.4
    assert d["window"]["length"] == 3


def test_ambiguous_effect_preserved():
    assert consequence_type_for_reaction("unknown") == \
        ConsequenceType.AMBIGUOUS_EFFECT
    assert consequence_type_for_reaction("no_effect") == \
        ConsequenceType.NO_OBSERVED_CHANGE


def test_no_invented_consequence():
    trace = ConsequenceTrace(
        consequence_type=ConsequenceType.NO_OBSERVED_CHANGE,
        action_refs=["A1"])
    assert "not invented" in trace.to_dict()["note"]
    assert any("not invented" in lim for lim in trace.limitations)


def test_reaction_to_consequence_mapping():
    assert consequence_type_for_reaction("prediction_confirmed") == \
        ConsequenceType.PREDICTION_OUTCOME
    assert consequence_type_for_reaction("blocked_by_safety") == \
        ConsequenceType.UNSAFE_BLOCK
