"""SensoryHomeostasisRegulator: lower novelty on noise; recover neglected; no ctl."""

from __future__ import annotations

from dataclasses import dataclass

from solaris_ai_nn.perceptual_metabolism import SensoryHomeostasisRegulator
from solaris_ai_nn.perceptual_metabolism.sensory_homeostasis import (
    HomeostaticAction,
)
from solaris_ai_nn.plural_sensorium.sensory_field import SensoryFieldState


@dataclass
class _Receptor:
    receptor_id: str = "r"
    modality: str = "radio_frequency"
    event_count: int = 5
    saturation: float = 0.2
    fatigue: float = 0.2
    reliability: float = 1.0
    recent_intensity: float = 0.5


def _field(**kw):
    base = dict(tick=1, active_modalities=["radio_frequency"],
                active_receptors=1, field_pressure=0.5, noise_pressure=0.2,
                absence_pressure=0.1, novelty_pressure=0.4, rhythm_pressure=0.3,
                cross_modal_pressure=0.4, uncertainty_pressure=0.1,
                saturation=0.2, fatigue=0.2, stability=0.7,
                dominant_modality="radio_frequency", neglected_modality=None,
                field_tensions=[])
    base.update(kw)
    return SensoryFieldState(**base)


def test_overload_lowers_novelty_sensitivity():
    state = SensoryHomeostasisRegulator().regulate(
        _field(noise_pressure=0.9), [_Receptor()])
    actions = {r.action for r in state.recommendations}
    assert HomeostaticAction.LOWER_NOVELTY_SENSITIVITY in actions


def test_neglected_modality_recovery_recommended():
    neglected = _Receptor(recent_intensity=0.0)
    state = SensoryHomeostasisRegulator().regulate(_field(), [neglected])
    actions = {r.action for r in state.recommendations}
    assert HomeostaticAction.RESTORE_NEGLECTED_MODALITY in actions


def test_no_external_control_action():
    state = SensoryHomeostasisRegulator().regulate(
        _field(noise_pressure=0.9), [_Receptor()])
    for r in state.recommendations:
        # No recommendation is a hardware/feeder control action.
        assert "start" not in r.action
        assert "hardware" not in r.action
    assert "no external control" in state.to_dict()["note"]


def test_novelty_starvation_raises_sensitivity():
    state = SensoryHomeostasisRegulator().regulate(
        _field(novelty_pressure=0.0), [_Receptor()])
    actions = {r.action for r in state.recommendations}
    assert HomeostaticAction.RAISE_NOVELTY_SENSITIVITY in actions
