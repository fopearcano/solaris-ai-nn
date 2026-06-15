"""PushFormationEngine: push from failed prediction; decays; evidence preserved."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    PushFormationEngine,
    PushSource,
    ValenceGradient,
    ValenceSource,
)


def test_push_forms_from_failed_prediction():
    g = ValenceGradient()
    g.add(ValenceSource.PREDICTION_FAILURE, 0.7, ["cognition:failed"])
    pushes = PushFormationEngine().form(g)
    assert pushes
    assert pushes[0].source_type == PushSource.FAILED_PREDICTION


def test_push_decays():
    g = ValenceGradient()
    g.add(ValenceSource.SENSORY_NOVELTY, 0.5)
    push = PushFormationEngine().form(g)[0]
    before = push.intensity
    push.decay()
    assert push.intensity < before


def test_evidence_refs_preserved():
    g = ValenceGradient()
    g.add(ValenceSource.LOGOS_TENSION, 0.6, ["logos:t1"])
    push = PushFormationEngine().form(g)[0]
    assert "logos:t1" in push.evidence_refs
    assert "not conscious intention" in push.to_dict()["note"]


def test_zero_magnitude_forms_no_push():
    g = ValenceGradient()
    g.add(ValenceSource.SENSORY_NOVELTY, 0.0)
    assert PushFormationEngine().form(g) == []
