"""PerceptualNeedModel: states update; trends; no feeling/consciousness language."""

from __future__ import annotations

from solaris_ai_nn.perceptual_metabolism import (
    PerceptualNeedModel,
    PerceptualNeedType,
)
from solaris_ai_nn.plural_sensorium.sensory_field import SensoryFieldState


def _field(**kw):
    base = dict(tick=1, active_modalities=["radio_frequency"],
                active_receptors=1, field_pressure=0.5, noise_pressure=0.2,
                absence_pressure=0.1, novelty_pressure=0.6, rhythm_pressure=0.3,
                cross_modal_pressure=0.2, uncertainty_pressure=0.1,
                saturation=0.2, fatigue=0.1, stability=0.7,
                dominant_modality="radio_frequency", neglected_modality=None,
                field_tensions=[])
    base.update(kw)
    return SensoryFieldState(**base)


def test_need_states_update():
    model = PerceptualNeedModel()
    model.update(_field(novelty_pressure=0.9), [], tick=1)
    novelty = model.get(PerceptualNeedType.NOVELTY)
    # High novelty pressure -> low novelty *need*.
    assert novelty.pressure < 0.2


def test_pressure_trends_work():
    model = PerceptualNeedModel()
    model.update(_field(absence_pressure=0.1), [], tick=1)
    model.update(_field(absence_pressure=0.8), [], tick=2)
    absence = model.get(PerceptualNeedType.ABSENCE_RESOLUTION)
    assert absence.pressure > 0.5
    assert absence.trend > 0.0


def test_dominant_need():
    model = PerceptualNeedModel()
    model.update(_field(field_pressure=0.95, saturation=0.9), [], tick=1)
    dominant = model.dominant()
    assert dominant is not None
    assert 0.0 <= dominant.pressure <= 1.0


def test_no_feeling_language():
    model = PerceptualNeedModel()
    model.update(_field(), [], tick=1)
    blob = str(model.to_dict()).lower()
    assert "not feelings" in blob
    for forbidden in ("emotion", "suffers", "happy", "sad"):
        # The model never describes needs as emotions.
        assert forbidden not in model.to_dict()["needs"].keys()


def test_needs_are_operational_note():
    need = PerceptualNeedModel().get(PerceptualNeedType.RECOVERY)
    assert "not a feeling" in need.to_dict()["note"]
