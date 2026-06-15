"""MotivationField: updates; inhibited/deferred/no-op tracked; no anthropomorphism."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    DesireCandidate,
    DesireKind,
    DesireStatus,
    MotivationField,
    PushFormationEngine,
    ValenceGradient,
    ValenceSource,
)


def _pushes():
    g = ValenceGradient()
    g.add(ValenceSource.SENSORY_NOVELTY, 0.7)
    g.add(ValenceSource.PREDICTION_FAILURE, 0.5)
    return PushFormationEngine().form(g), g


def test_motivation_field_updates():
    pushes, g = _pushes()
    desires = [DesireCandidate(kind=DesireKind.FOCUS_MODALITY)]
    state = MotivationField().build(pushes, desires, valence_gradient=g)
    assert state.active_push_count == len(pushes)
    assert state.dominant_pressure


def test_inhibited_deferred_no_op_tracked():
    pushes, g = _pushes()
    desires = [
        DesireCandidate(kind=DesireKind.FOCUS_MODALITY,
                        status=DesireStatus.INHIBITED),
        DesireCandidate(kind=DesireKind.INSPECT_ABSENCE,
                        status=DesireStatus.DEFERRED),
        DesireCandidate(kind=DesireKind.NO_ACTION),
    ]
    state = MotivationField().build(pushes, desires, valence_gradient=g)
    assert state.inhibited_desire_count == 1
    assert state.deferred_desire_count == 1
    assert state.no_action_pressure > 0.0


def test_no_anthropomorphic_claims():
    pushes, g = _pushes()
    state = MotivationField().build(pushes, [], valence_gradient=g)
    assert "not anthropomorphic motivation" in state.to_dict()["note"]
