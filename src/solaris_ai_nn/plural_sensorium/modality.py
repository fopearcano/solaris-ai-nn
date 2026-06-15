"""Plural sensorium modality model -- human-like, non-human, and machine-native.

A *plural* (or "alien") sensorium does not exclude human senses, nor does it
privilege them. Every modality -- text, light, RF, echo, vibration, magnetic
field, absence, interference -- is a first-class way the organism is bathed in
environmental flux. No modality is automatically privileged, and modality-native
structure is preserved rather than collapsed into human object labels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class ModalityFamily:
    HUMAN_TEXTUAL = "human_textual"
    HUMAN_VISUAL_METADATA = "human_visual_metadata"
    HUMAN_AUDIO_METADATA = "human_audio_metadata"
    LIGHT = "light"
    ORDINARY_TEMPERATURE = "ordinary_temperature"
    MOVEMENT = "movement"
    PRESSURE_TOUCH = "pressure_touch"
    RADIO_FREQUENCY = "radio_frequency"
    MICROWAVE_MMWAVE = "microwave_mmwave"
    ULTRASOUND_ECHO = "ultrasound_echo"
    VIBRATION = "vibration"
    MAGNETIC = "magnetic"
    THERMAL_GRADIENT = "thermal_gradient"
    BAROMETRIC_PRESSURE = "barometric_pressure"
    ELECTRIC_FIELD_LIKE = "electric_field_like"
    MACHINE_RHYTHM = "machine_rhythm"
    ABSENCE_SILENCE = "absence_silence"
    INTERFERENCE_NOISE = "interference_noise"
    UNKNOWN_FIELD = "unknown_field"

    ALL = (HUMAN_TEXTUAL, HUMAN_VISUAL_METADATA, HUMAN_AUDIO_METADATA, LIGHT,
           ORDINARY_TEMPERATURE, MOVEMENT, PRESSURE_TOUCH, RADIO_FREQUENCY,
           MICROWAVE_MMWAVE, ULTRASOUND_ECHO, VIBRATION, MAGNETIC,
           THERMAL_GRADIENT, BAROMETRIC_PRESSURE, ELECTRIC_FIELD_LIKE,
           MACHINE_RHYTHM, ABSENCE_SILENCE, INTERFERENCE_NOISE, UNKNOWN_FIELD)


class ModalityClass:
    HUMAN_LIKE = "human_like"
    NON_HUMAN = "non_human"
    MACHINE_NATIVE = "machine_native"
    ENVIRONMENTAL_META = "environmental_meta"
    ABSENCE_BASED = "absence_based"
    CROSS_MODAL = "cross_modal"

    ALL = (HUMAN_LIKE, NON_HUMAN, MACHINE_NATIVE, ENVIRONMENTAL_META,
           ABSENCE_BASED, CROSS_MODAL)


class ModalityStatus:
    ACTIVE = "active"
    DORMANT = "dormant"
    SATURATED = "saturated"
    FATIGUED = "fatigued"
    SILENT = "silent"
    UNRELIABLE = "unreliable"

    ALL = (ACTIVE, DORMANT, SATURATED, FATIGUED, SILENT, UNRELIABLE)


# Which class each family belongs to. Human families are valid but never the
# default; non-human and machine-native families carry equal first-class weight.
_FAMILY_CLASS = {
    ModalityFamily.HUMAN_TEXTUAL: ModalityClass.HUMAN_LIKE,
    ModalityFamily.HUMAN_VISUAL_METADATA: ModalityClass.HUMAN_LIKE,
    ModalityFamily.HUMAN_AUDIO_METADATA: ModalityClass.HUMAN_LIKE,
    ModalityFamily.LIGHT: ModalityClass.HUMAN_LIKE,
    ModalityFamily.ORDINARY_TEMPERATURE: ModalityClass.HUMAN_LIKE,
    ModalityFamily.MOVEMENT: ModalityClass.HUMAN_LIKE,
    ModalityFamily.PRESSURE_TOUCH: ModalityClass.HUMAN_LIKE,
    ModalityFamily.RADIO_FREQUENCY: ModalityClass.NON_HUMAN,
    ModalityFamily.MICROWAVE_MMWAVE: ModalityClass.NON_HUMAN,
    ModalityFamily.ULTRASOUND_ECHO: ModalityClass.NON_HUMAN,
    ModalityFamily.VIBRATION: ModalityClass.NON_HUMAN,
    ModalityFamily.MAGNETIC: ModalityClass.NON_HUMAN,
    ModalityFamily.THERMAL_GRADIENT: ModalityClass.NON_HUMAN,
    ModalityFamily.BAROMETRIC_PRESSURE: ModalityClass.ENVIRONMENTAL_META,
    ModalityFamily.ELECTRIC_FIELD_LIKE: ModalityClass.NON_HUMAN,
    ModalityFamily.MACHINE_RHYTHM: ModalityClass.MACHINE_NATIVE,
    ModalityFamily.ABSENCE_SILENCE: ModalityClass.ABSENCE_BASED,
    ModalityFamily.INTERFERENCE_NOISE: ModalityClass.ENVIRONMENTAL_META,
    ModalityFamily.UNKNOWN_FIELD: ModalityClass.NON_HUMAN,
}

# Source modality hints (used by the sensory-membrane bridge, section 21).
MODALITY_HINTS = {
    "human_textual": ModalityFamily.HUMAN_TEXTUAL,
    "human_visual_metadata": ModalityFamily.HUMAN_VISUAL_METADATA,
    "human_audio_metadata": ModalityFamily.HUMAN_AUDIO_METADATA,
    "alien_rf": ModalityFamily.RADIO_FREQUENCY,
    "alien_echo": ModalityFamily.ULTRASOUND_ECHO,
    "alien_thermal": ModalityFamily.THERMAL_GRADIENT,
    "alien_vibration": ModalityFamily.VIBRATION,
    "alien_magnetic": ModalityFamily.MAGNETIC,
    "alien_pressure": ModalityFamily.BAROMETRIC_PRESSURE,
    "alien_field": ModalityFamily.ELECTRIC_FIELD_LIKE,
    "machine_rhythm": ModalityFamily.MACHINE_RHYTHM,
    "absence_silence": ModalityFamily.ABSENCE_SILENCE,
}


@dataclass
class SensoriumModality:
    """One modality: its family, its class, and its current status."""

    family: str = ModalityFamily.UNKNOWN_FIELD
    status: str = ModalityStatus.ACTIVE
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.family not in ModalityFamily.ALL:
            self.family = ModalityFamily.UNKNOWN_FIELD
        if self.status not in ModalityStatus.ALL:
            self.status = ModalityStatus.ACTIVE

    @property
    def modality_class(self) -> str:
        return _FAMILY_CLASS.get(self.family, ModalityClass.NON_HUMAN)

    @property
    def is_human_like(self) -> bool:
        return self.modality_class == ModalityClass.HUMAN_LIKE

    @property
    def is_non_human(self) -> bool:
        return self.modality_class in (ModalityClass.NON_HUMAN,
                                       ModalityClass.MACHINE_NATIVE)

    def to_dict(self) -> Dict[str, Any]:
        return {"family": self.family, "modality_class": self.modality_class,
                "status": self.status, "is_human_like": self.is_human_like,
                "is_non_human": self.is_non_human, "notes": list(self.notes)}


def modality_class_for(family: str) -> str:
    return _FAMILY_CLASS.get(family, ModalityClass.NON_HUMAN)


def family_for_hint(hint: str) -> str:
    """Map a sensory-membrane modality hint to a plural-sensorium family."""
    return MODALITY_HINTS.get(hint, ModalityFamily.UNKNOWN_FIELD)
