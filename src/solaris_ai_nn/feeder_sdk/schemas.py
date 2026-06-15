"""Feature schemas -- the recommended feature shape per modality event.

Each :class:`FeatureSchema` documents the required and optional feature keys, the
recommended units, the value types, the privacy notes, and the contamination
risks for one event type. Schemas avoid semantic labels (those are annotation-only
and never ground truth), make units explicit, and forbid decoded private content
or raw recordings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contract import FeederSDKModality as M


@dataclass
class FeatureSchema:
    event_type: str
    modality: str
    required_keys: List[str] = field(default_factory=list)
    optional_keys: List[str] = field(default_factory=list)
    units: Dict[str, str] = field(default_factory=dict)
    value_types: Dict[str, str] = field(default_factory=dict)
    privacy_notes: List[str] = field(default_factory=list)
    contamination_risks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    def validate_features(self, features: Dict[str, Any]) -> List[str]:
        """Return a list of issues (missing required keys / bad types)."""
        issues: List[str] = []
        for key in self.required_keys:
            if key not in features:
                issues.append(f"missing required feature {key!r}")
        for key, expected in self.value_types.items():
            if key in features and expected == "number" \
                    and not isinstance(features[key], (int, float, bool)):
                issues.append(f"feature {key!r} should be a number")
        return issues


_SCHEMAS: Dict[str, FeatureSchema] = {}


def _add(schema: FeatureSchema) -> None:
    _SCHEMAS[schema.event_type] = schema


_add(FeatureSchema(
    "human_textual_event", M.HUMAN_TEXTUAL,
    required_keys=["length"], optional_keys=["token_count", "char_entropy"],
    units={"length": "characters"}, value_types={"length": "number"},
    privacy_notes=["may contain human text; mark contains_human_text"],
    contamination_risks=["human annotation can become a label if misused"]))
_add(FeatureSchema(
    "human_visual_metadata_event", M.HUMAN_VISUAL_METADATA,
    required_keys=["brightness"], optional_keys=["motion_estimate",
                                                 "region_count"],
    units={"brightness": "normalized_0_1"},
    value_types={"brightness": "number"},
    privacy_notes=["metadata only; never raw images by default"],
    contamination_risks=["object labels must be annotation-only"]))
_add(FeatureSchema(
    "human_audio_metadata_event", M.HUMAN_AUDIO_METADATA,
    required_keys=["loudness"], optional_keys=["band_energy", "onset_rate"],
    units={"loudness": "normalized_0_1"}, value_types={"loudness": "number"},
    privacy_notes=["metadata only; never raw speech by default"],
    contamination_risks=["speech transcription is out of scope"]))
_add(FeatureSchema(
    "light_temperature_event", M.LIGHT,
    required_keys=["lux"], optional_keys=["celsius"],
    units={"lux": "normalized_0_1", "celsius": "degrees_C"},
    value_types={"lux": "number", "celsius": "number"},
    privacy_notes=["ambient environment only"], contamination_risks=[]))
_add(FeatureSchema(
    "rf_feature_event", M.RADIO_FREQUENCY,
    required_keys=["power"],
    optional_keys=["band", "noise_floor", "burstiness", "drift", "periodicity"],
    units={"power": "normalized_0_1", "band": "GHz"},
    value_types={"power": "number", "band": "number"},
    privacy_notes=["features only; NEVER decode communication content"],
    contamination_risks=["decoded private content is forbidden"]))
_add(FeatureSchema(
    "echo_reflection_event", M.ULTRASOUND_ECHO,
    required_keys=["boundary"],
    optional_keys=["distance_estimate", "reflectivity", "doppler_shift",
                   "cluster_count"],
    units={"distance_estimate": "meters"},
    value_types={"boundary": "number", "distance_estimate": "number"},
    privacy_notes=["reflection metadata; no person/object identity"],
    contamination_risks=["person/object labels must be annotation-only"]))
_add(FeatureSchema(
    "vibration_event", M.VIBRATION,
    required_keys=["amplitude"], optional_keys=["frequency", "rhythm_period"],
    units={"frequency": "Hz", "rhythm_period": "seconds"},
    value_types={"amplitude": "number", "frequency": "number"},
    privacy_notes=["mechanical vibration features only"],
    contamination_risks=[]))
_add(FeatureSchema(
    "magnetic_event", M.MAGNETIC,
    required_keys=["field"], optional_keys=["drift", "anomaly"],
    units={"field": "normalized_or_uT"}, value_types={"field": "number"},
    privacy_notes=["field magnitude features only"], contamination_risks=[]))
_add(FeatureSchema(
    "thermal_gradient_event", M.THERMAL_GRADIENT,
    required_keys=["gradient"], optional_keys=["drift", "hotspot_count"],
    units={"gradient": "degrees_C_per_unit"},
    value_types={"gradient": "number"},
    privacy_notes=["thermal summary; no thermal imagery of people"],
    contamination_risks=["thermal person-detection must be annotation-only"]))
_add(FeatureSchema(
    "pressure_event", M.BAROMETRIC_PRESSURE,
    required_keys=["pressure"], optional_keys=["drift"],
    units={"pressure": "hPa"}, value_types={"pressure": "number"},
    privacy_notes=["ambient pressure only"], contamination_risks=[]))
_add(FeatureSchema(
    "machine_rhythm_event", M.MACHINE_RHYTHM,
    required_keys=["load_proxy"], optional_keys=["time_phase_sin",
                                                 "time_phase_cos", "file_count"],
    units={}, value_types={"load_proxy": "number"},
    privacy_notes=["local machine rhythm; no privileged data"],
    contamination_risks=[]))
_add(FeatureSchema(
    "absence_silence_event", M.ABSENCE_SILENCE,
    required_keys=["silent_sources"], optional_keys=["elapsed_s"],
    units={"elapsed_s": "seconds"}, value_types={"silent_sources": "number"},
    privacy_notes=["absence is a perceptual signal, not content"],
    contamination_risks=[]))
_add(FeatureSchema(
    "interference_noise_event", M.INTERFERENCE_NOISE,
    required_keys=["noise_level"], optional_keys=["burst"],
    units={"noise_level": "normalized_0_1"},
    value_types={"noise_level": "number"},
    privacy_notes=["noise features only"], contamination_risks=[]))
_add(FeatureSchema(
    "cross_modal_hint_event", M.UNKNOWN_FIELD,
    required_keys=["relation"], optional_keys=["lag_s", "modality_a",
                                               "modality_b"],
    units={"lag_s": "seconds"}, value_types={"lag_s": "number"},
    privacy_notes=["a hint only; never asserted as ground truth"],
    contamination_risks=["cross-modal hints must not impose object ontology"]))


FEATURE_SCHEMAS: Dict[str, FeatureSchema] = dict(_SCHEMAS)


def get_schema(event_type: str) -> Optional[FeatureSchema]:
    return FEATURE_SCHEMAS.get(event_type)


def schema_for_modality(modality: str) -> Optional[FeatureSchema]:
    for schema in FEATURE_SCHEMAS.values():
        if schema.modality == modality:
            return schema
    return None


def all_event_types() -> List[str]:
    return sorted(FEATURE_SCHEMAS)


def schema_coverage() -> float:
    """Fraction of the contract's modalities that have a documented schema."""
    covered = {s.modality for s in FEATURE_SCHEMAS.values()}
    return round(len(covered & set(M.ALL)) / len(M.ALL), 4)
