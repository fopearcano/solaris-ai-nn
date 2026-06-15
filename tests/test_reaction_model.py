"""SensoriumReaction: serializes; valence operational only; no feeling language."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import (
    ActionCandidateRecord,
    ActionKind,
    ReactionAssessment,
    ReactionKind,
    ReactionValence,
    SensoriumReaction,
)


def test_reaction_serializes():
    r = SensoriumReaction(kind=ReactionKind.UNCERTAINTY_REDUCED,
                          action_ref="A1")
    d = r.to_dict()
    assert d["kind"] == ReactionKind.UNCERTAINTY_REDUCED
    assert d["valence"] == ReactionValence.CONSTRUCTIVE


def test_valence_operational_only():
    r = SensoriumReaction(kind=ReactionKind.OVERLOAD_REDUCED)
    assert r.valence == ReactionValence.STABILIZING
    assert "operational effect" in r.to_dict()["note"]


def test_no_feeling_language():
    r = SensoriumReaction(kind=ReactionKind.UNCERTAINTY_REDUCED)
    note = r.to_dict()["note"].lower()
    assert "not feeling" in note
    assert "pleasure" not in note or "not" in note


def test_blocked_action_produces_reaction():
    blocked = ActionCandidateRecord(kind="actuate_robot")
    blocked.status = "blocked"
    r = ReactionAssessment().assess(blocked, before={}, after={})
    assert r.kind == ReactionKind.BLOCKED_BY_SAFETY


def test_constructive_action_reduces_uncertainty():
    a = ActionCandidateRecord(kind=ActionKind.SHIFT_ATTENTION)
    r = ReactionAssessment().assess(a, before={"uncertainty": 0.6},
                                    after={"uncertainty": 0.4})
    assert r.kind == ReactionKind.UNCERTAINTY_REDUCED
    assert r.magnitude > 0.0
