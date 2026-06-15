"""Desire-formation SensoriumValence: operational; no feeling/emotion language."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    ValenceAssessment,
    ValenceDirection,
    ValenceGradient,
    ValenceSource,
)


def test_valence_gradients_serialize():
    g = ValenceGradient()
    g.add(ValenceSource.SENSORY_NOVELTY, 0.6, ["e1"])
    g.add(ValenceSource.SENSORY_OVERLOAD, 0.8, ["e2"])
    d = g.to_dict()
    assert d["valence_count"] == 2
    assert d["dominant_direction"] in ValenceDirection.ALL


def test_valence_is_operational():
    g = ValenceGradient()
    v = g.add(ValenceSource.SENSORY_NOVELTY, 0.5)
    assert v.direction == ValenceDirection.ATTRACTIVE
    assert "operational priority" in v.to_dict()["note"].lower()


def test_no_feeling_or_emotion_language():
    g = ValenceGradient()
    g.add(ValenceSource.SENSORY_OVERLOAD, 0.5)
    assert "not emotion" in g.to_dict()["note"].lower()


def test_assess_from_upstream_states():
    g = ValenceAssessment().assess(
        metabolism={"overload_state": True, "deprivation_state": True},
        cognition={"failed_prediction_count": 2},
        self_boundary={"continuity_break_count": 1}, logos_tension_count=1)
    sources = {v.source for v in g.valences}
    assert ValenceSource.SENSORY_OVERLOAD in sources
    assert ValenceSource.PREDICTION_FAILURE in sources
    assert ValenceSource.LOGOS_TENSION in sources


def test_cannot_authorize_real_world_action():
    v = ValenceGradient().add(ValenceSource.SENSORY_NOVELTY, 0.5)
    assert not hasattr(v, "actuate")
    assert not hasattr(v, "execute")
