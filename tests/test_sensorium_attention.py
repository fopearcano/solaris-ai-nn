"""SensoriumAttentionPolicy: focus / damp internally; no hardware control."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import (
    Receptor,
    SensoriumAttentionPolicy,
    SensoryField,
)
from solaris_ai_nn.plural_sensorium.attention import AttentionAction
from solaris_ai_nn.plural_sensorium.event_envelope import SensoryEventEnvelope


def _receptor(power, modality="radio_frequency"):
    r = Receptor(receptor_id=modality, modality=modality, source_id=modality)
    r.observe(SensoryEventEnvelope(source_id=modality, source_kind="fixture_replay",
                                   modality=modality, features={"power": power}))
    return r


def test_attention_can_focus_modality():
    policy = SensoriumAttentionPolicy()
    shift = policy.focus("radio_frequency")
    assert shift.action == AttentionAction.FOCUS_MODALITY
    assert policy.state.focus_modality == "radio_frequency"
    assert policy.state.modality_priority["radio_frequency"] == 1.0


def test_noisy_modality_reduced_internally():
    policy = SensoriumAttentionPolicy()
    field = SensoryField()
    r = _receptor(0.5)
    state = field.update([r], noise=0.9)
    shifts = policy.decide(state, [r])
    assert any(s.action == AttentionAction.REDUCE_NOISY_MODALITY for s in shifts)


def test_no_hardware_control():
    policy = SensoriumAttentionPolicy()
    assert policy.state.controls_hardware is False
    assert policy.snapshot()["controls_hardware"] is False
    # No method exists to start or control an external sensor.
    assert not hasattr(policy, "start_sensor")
    assert not hasattr(policy, "control_hardware")


def test_attention_is_bounded():
    policy = SensoriumAttentionPolicy(max_shifts_per_tick=2)
    field = SensoryField()
    rs = [_receptor(2.0, "radio_frequency"), _receptor(2.0, "vibration")]
    state = field.update(rs, novelty=0.9, noise=0.9, absence=0.9)
    shifts = policy.decide(state, rs)
    assert len(shifts) <= 2
