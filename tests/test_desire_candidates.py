"""DesireCandidate: serializes; hardware/source impossible; no human wanting."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    DesireCandidate,
    DesireFormationEngine,
    DesireKind,
    PushFormationEngine,
    ValenceGradient,
    ValenceSource,
)
from solaris_ai_nn.desire_formation.internal_actions import InternalActionKind


def test_desire_candidate_serializes():
    d = DesireCandidate(kind=DesireKind.INSPECT_ABSENCE, confidence=0.6)
    out = d.to_dict()
    assert out["kind"] == DesireKind.INSPECT_ABSENCE
    assert out["safety_scope"] == "internal_only"
    assert "not human wanting" in out["note"]


def test_expected_action_is_internal_only():
    for kind in DesireKind.ALL:
        d = DesireCandidate(kind=kind)
        # Every desire kind maps to an allowed internal action (or no_op).
        assert d.expected_internal_action in InternalActionKind.ALL


def test_human_wanting_language_absent():
    d = DesireCandidate(kind=DesireKind.FOCUS_MODALITY)
    note = " ".join(d.limitations).lower()
    assert "not human wanting" in note
    assert "internal-only" in note


def test_formed_from_pushes():
    g = ValenceGradient()
    g.add(ValenceSource.PREDICTION_FAILURE, 0.7)
    pushes = PushFormationEngine().form(g)
    desires = DesireFormationEngine().form(pushes)
    assert desires
    assert desires[0].kind == DesireKind.TEST_PREDICTION
