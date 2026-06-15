"""Sensorium profiles -- the perceptual configuration each study arm runs under.

A :class:`SensoriumProfile` pins which modalities are enabled, whether receptors
adapt, which attention policy is used, whether human labels are allowed, and
whether a live source is required. Human-like, non-human, machine-native, and
mixed profiles are all valid; none is privileged as the default truth; and human
labels are *always* annotations, never ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..plural_sensorium.modality import ModalityFamily as MF


class SensoriumProfileType:
    HUMAN_LIKE_TEXT_LIGHT_TEMPERATURE = "human_like_text_light_temperature"
    HUMAN_LIKE_AUDIO_VISUAL_METADATA = "human_like_audio_visual_metadata"
    RF_ECHO_VIBRATION_MAGNETIC = "rf_echo_vibration_magnetic"
    THERMAL_PRESSURE_MACHINE_RHYTHM = "thermal_pressure_machine_rhythm"
    ABSENCE_SILENCE_DOMINANT = "absence_silence_dominant"
    MIXED_HUMAN_NONHUMAN = "mixed_human_nonhuman"
    FEATURE_ONLY_NO_LABELS = "feature_only_no_labels"
    HUMAN_LABEL_CONTAMINATED = "human_label_contaminated"
    PASSIVE_EVENT_LIST = "passive_event_list"
    ADAPTIVE_RECEPTOR_FIELD = "adaptive_receptor_field"

    ALL = (HUMAN_LIKE_TEXT_LIGHT_TEMPERATURE, HUMAN_LIKE_AUDIO_VISUAL_METADATA,
           RF_ECHO_VIBRATION_MAGNETIC, THERMAL_PRESSURE_MACHINE_RHYTHM,
           ABSENCE_SILENCE_DOMINANT, MIXED_HUMAN_NONHUMAN,
           FEATURE_ONLY_NO_LABELS, HUMAN_LABEL_CONTAMINATED,
           PASSIVE_EVENT_LIST, ADAPTIVE_RECEPTOR_FIELD)


# Which modality families each profile type enables.
_PROFILE_MODALITIES = {
    SensoriumProfileType.HUMAN_LIKE_TEXT_LIGHT_TEMPERATURE:
        [MF.HUMAN_TEXTUAL, MF.LIGHT, MF.ORDINARY_TEMPERATURE],
    SensoriumProfileType.HUMAN_LIKE_AUDIO_VISUAL_METADATA:
        [MF.HUMAN_AUDIO_METADATA, MF.HUMAN_VISUAL_METADATA],
    SensoriumProfileType.RF_ECHO_VIBRATION_MAGNETIC:
        [MF.RADIO_FREQUENCY, MF.ULTRASOUND_ECHO, MF.VIBRATION, MF.MAGNETIC],
    SensoriumProfileType.THERMAL_PRESSURE_MACHINE_RHYTHM:
        [MF.THERMAL_GRADIENT, MF.BAROMETRIC_PRESSURE, MF.MACHINE_RHYTHM],
    SensoriumProfileType.ABSENCE_SILENCE_DOMINANT:
        [MF.RADIO_FREQUENCY, MF.VIBRATION, MF.ABSENCE_SILENCE],
    SensoriumProfileType.MIXED_HUMAN_NONHUMAN:
        [MF.HUMAN_TEXTUAL, MF.RADIO_FREQUENCY, MF.VIBRATION, MF.MACHINE_RHYTHM],
    SensoriumProfileType.FEATURE_ONLY_NO_LABELS:
        [MF.RADIO_FREQUENCY, MF.VIBRATION, MF.THERMAL_GRADIENT],
    SensoriumProfileType.HUMAN_LABEL_CONTAMINATED:
        [MF.HUMAN_TEXTUAL, MF.RADIO_FREQUENCY],
    SensoriumProfileType.PASSIVE_EVENT_LIST:
        [MF.RADIO_FREQUENCY, MF.VIBRATION],
    SensoriumProfileType.ADAPTIVE_RECEPTOR_FIELD:
        [MF.HUMAN_TEXTUAL, MF.RADIO_FREQUENCY, MF.ULTRASOUND_ECHO,
         MF.VIBRATION],
}


@dataclass
class SensoriumProfile:
    """One perceptual configuration for a study arm."""

    profile_type: str
    enabled_modalities: List[str] = field(default_factory=list)
    allowed_feeder_sources: List[str] = field(default_factory=list)
    receptor_adaptation_enabled: bool = True
    attention_policy: str = "adaptive"  # "adaptive" | "fixed"
    baseline_learning_enabled: bool = True
    cross_modal_detection_enabled: bool = True
    human_labels_allowed: bool = False
    live_source_required: bool = False
    passive_only: bool = False
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # A hard guarantee, never configurable.
    human_labels_as_ground_truth: bool = False

    def __post_init__(self) -> None:
        if self.profile_type not in SensoriumProfileType.ALL:
            self.profile_type = SensoriumProfileType.MIXED_HUMAN_NONHUMAN
        if not self.enabled_modalities:
            self.enabled_modalities = list(
                _PROFILE_MODALITIES.get(self.profile_type, []))
        # Human labels are never ground truth, regardless of configuration.
        self.human_labels_as_ground_truth = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_type": self.profile_type,
            "enabled_modalities": list(self.enabled_modalities),
            "allowed_feeder_sources": list(self.allowed_feeder_sources),
            "receptor_adaptation_enabled": self.receptor_adaptation_enabled,
            "attention_policy": self.attention_policy,
            "baseline_learning_enabled": self.baseline_learning_enabled,
            "cross_modal_detection_enabled": self.cross_modal_detection_enabled,
            "human_labels_allowed": self.human_labels_allowed,
            "human_labels_as_ground_truth": False,
            "live_source_required": self.live_source_required,
            "passive_only": self.passive_only,
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }


@dataclass
class SensoriumProfileBuilder:
    """Builds the canonical sensorium profiles by type."""

    def build(self, profile_type: str) -> SensoriumProfile:
        kw: Dict[str, Any] = {"profile_type": profile_type}
        if profile_type == SensoriumProfileType.HUMAN_LABEL_CONTAMINATED:
            kw["human_labels_allowed"] = True
        if profile_type == SensoriumProfileType.FEATURE_ONLY_NO_LABELS:
            kw["human_labels_allowed"] = False
        if profile_type == SensoriumProfileType.PASSIVE_EVENT_LIST:
            kw["passive_only"] = True
            kw["receptor_adaptation_enabled"] = False
            kw["baseline_learning_enabled"] = False
            kw["cross_modal_detection_enabled"] = False
            kw["attention_policy"] = "fixed"
        return SensoriumProfile(**kw)

    def build_all(self) -> Dict[str, SensoriumProfile]:
        return {t: self.build(t) for t in SensoriumProfileType.ALL}
