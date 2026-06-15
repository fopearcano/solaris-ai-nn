"""InhibitionEngine: safety/uncertainty/no-effect-history inhibition recorded."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import InhibitionEngine, InhibitionReason


def test_safety_inhibition():
    engine = InhibitionEngine()
    inh = engine.inhibit(InhibitionReason.SAFETY_RISK, action_ref="A1",
                         action_kind="actuate_robot")
    assert inh.reason == InhibitionReason.SAFETY_RISK
    assert "not failure" in inh.to_dict()["note"]


def test_uncertainty_inhibition():
    engine = InhibitionEngine()
    engine.inhibit(InhibitionReason.BOUNDARY_UNCERTAIN, action_ref="A2")
    assert engine.distribution()[InhibitionReason.BOUNDARY_UNCERTAIN] == 1


def test_no_effect_history_inhibition():
    engine = InhibitionEngine()
    engine.inhibit(InhibitionReason.NO_EFFECT_HISTORY, action_ref="A3")
    assert len(engine.inhibitions) == 1
    assert engine.inhibitions[0].reason == InhibitionReason.NO_EFFECT_HISTORY


def test_unknown_reason_fallback():
    engine = InhibitionEngine()
    inh = engine.inhibit("not_a_real_reason")
    assert inh.reason == InhibitionReason.UNKNOWN
