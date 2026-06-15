"""SensoriumModality: human-like and non-human valid; none privileged."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import (
    ModalityClass,
    ModalityFamily,
    SensoriumModality,
    modality_class_for,
)


def test_human_like_modalities_exist():
    for fam in (ModalityFamily.HUMAN_TEXTUAL, ModalityFamily.LIGHT,
                ModalityFamily.MOVEMENT, ModalityFamily.PRESSURE_TOUCH):
        m = SensoriumModality(family=fam)
        assert m.is_human_like


def test_non_human_modalities_exist():
    for fam in (ModalityFamily.RADIO_FREQUENCY, ModalityFamily.ULTRASOUND_ECHO,
                ModalityFamily.MAGNETIC, ModalityFamily.MACHINE_RHYTHM):
        m = SensoriumModality(family=fam)
        assert m.is_non_human


def test_no_modality_privileged_by_default():
    # No modality class is the "default"; every family maps to a real class,
    # and human-like is not special-cased above the others.
    classes = {modality_class_for(f) for f in ModalityFamily.ALL}
    assert ModalityClass.HUMAN_LIKE in classes
    assert ModalityClass.NON_HUMAN in classes
    assert ModalityClass.MACHINE_NATIVE in classes
    # Human-like is not the majority by construction (non-human + others
    # together outnumber human-like families).
    human = sum(1 for f in ModalityFamily.ALL
                if modality_class_for(f) == ModalityClass.HUMAN_LIKE)
    assert human < len(ModalityFamily.ALL) - human


def test_absence_is_a_modality():
    m = SensoriumModality(family=ModalityFamily.ABSENCE_SILENCE)
    assert m.modality_class == ModalityClass.ABSENCE_BASED
