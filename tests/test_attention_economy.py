"""AttentionEconomy: finite; explainable; neglected-modality recovery reserved."""

from __future__ import annotations

from dataclasses import dataclass

from solaris_ai_nn.perceptual_metabolism import AttentionEconomy, PerceptualNeedModel
from solaris_ai_nn.perceptual_metabolism.attention_economy import AttentionTarget
from solaris_ai_nn.plural_sensorium.sensory_field import SensoryFieldState


@dataclass
class _Receptor:
    receptor_id: str = "r"
    modality: str = "radio_frequency"
    fatigue: float = 0.2


def _field():
    return SensoryFieldState(
        tick=1, active_modalities=["radio_frequency"], active_receptors=1,
        field_pressure=0.5, noise_pressure=0.2, absence_pressure=0.4,
        novelty_pressure=0.6, rhythm_pressure=0.3, cross_modal_pressure=0.3,
        uncertainty_pressure=0.1, saturation=0.2, fatigue=0.2, stability=0.7,
        dominant_modality="radio_frequency", neglected_modality=None,
        field_tensions=[])


def test_attention_finite():
    econ = AttentionEconomy(total_budget=1.0)
    state = econ.allocate(_field(), [_Receptor()], PerceptualNeedModel())
    total = sum(a.weight for a in state.allocations)
    # Weights are rounded to 4 decimals, so allow that rounding slack.
    assert total <= 1.0 + 1e-3


def test_allocation_explainable():
    state = AttentionEconomy().allocate(_field(), [_Receptor()],
                                        PerceptualNeedModel())
    assert state.allocations
    assert all(a.reason for a in state.allocations)


def test_neglected_modality_recovery_exists():
    state = AttentionEconomy(neglected_recovery_fraction=0.1).allocate(
        _field(), [_Receptor()], PerceptualNeedModel())
    targets = {a.target_type for a in state.allocations}
    assert AttentionTarget.NEGLECTED_MODALITY_RECOVERY in targets
    assert state.neglected_recovery_reserved > 0.0


def test_no_sensor_control_note():
    state = AttentionEconomy().allocate(_field(), [_Receptor()],
                                        PerceptualNeedModel())
    assert "no sensor control" in state.to_dict()["note"]
