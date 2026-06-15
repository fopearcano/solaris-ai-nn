"""External feeder SDK contract -- the data shape an artificial sensory organ emits.

A feeder is *outside* Solaris: a separate process that converts real environmental
phenomena into :class:`FeederSDKEnvelope` records (JSONL) which Solaris reads
read-only. The envelope is compatible with the Prompt-41 Sensory Event Envelope
and the Prompt-43 LiveFeederEnvelope, and adds privacy flags, safety flags, and a
schema version. Features are primary; human labels are always external and never
ground truth; sensory text is never a command; provenance is mandatory.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "feeder-sdk/1.0"


class FeederSDKModality:
    HUMAN_TEXTUAL = "human_textual"
    HUMAN_VISUAL_METADATA = "human_visual_metadata"
    HUMAN_AUDIO_METADATA = "human_audio_metadata"
    LIGHT = "light"
    ORDINARY_TEMPERATURE = "ordinary_temperature"
    RADIO_FREQUENCY = "radio_frequency"
    MICROWAVE_MMWAVE = "microwave_mmwave"
    ULTRASOUND_ECHO = "ultrasound_echo"
    VIBRATION = "vibration"
    MAGNETIC = "magnetic"
    THERMAL_GRADIENT = "thermal_gradient"
    BAROMETRIC_PRESSURE = "barometric_pressure"
    MACHINE_RHYTHM = "machine_rhythm"
    ABSENCE_SILENCE = "absence_silence"
    INTERFERENCE_NOISE = "interference_noise"
    UNKNOWN_FIELD = "unknown_field"

    ALL = (HUMAN_TEXTUAL, HUMAN_VISUAL_METADATA, HUMAN_AUDIO_METADATA, LIGHT,
           ORDINARY_TEMPERATURE, RADIO_FREQUENCY, MICROWAVE_MMWAVE,
           ULTRASOUND_ECHO, VIBRATION, MAGNETIC, THERMAL_GRADIENT,
           BAROMETRIC_PRESSURE, MACHINE_RHYTHM, ABSENCE_SILENCE,
           INTERFERENCE_NOISE, UNKNOWN_FIELD)


class FeederSDKAnnotationStatus:
    NONE = "none"
    EXTERNAL_NON_GROUND_TRUTH = "external_non_ground_truth"
    HUMAN_LABEL_EXTERNAL = "human_label_external"
    GENERATED_BY_FEEDER = "generated_by_feeder"
    UNKNOWN = "unknown"

    ALL = (NONE, EXTERNAL_NON_GROUND_TRUTH, HUMAN_LABEL_EXTERNAL,
           GENERATED_BY_FEEDER, UNKNOWN)
    HUMAN_LABELLED = frozenset({HUMAN_LABEL_EXTERNAL})


class FeederSDKTrustLevel:
    UNTRUSTED = "untrusted"
    SIMULATED_FIXTURE = "simulated_fixture"
    LOCAL_MANUAL = "local_manual"
    LOCAL_SCRIPT = "local_script"
    EXTERNAL_FEATURE_ONLY = "external_feature_only"
    UNVERIFIED_EXTERNAL = "unverified_external"

    ALL = (UNTRUSTED, SIMULATED_FIXTURE, LOCAL_MANUAL, LOCAL_SCRIPT,
           EXTERNAL_FEATURE_ONLY, UNVERIFIED_EXTERNAL)


@dataclass
class FeederSDKSource:
    """Describes the origin of a feeder stream (still read-only to Solaris)."""

    source_id: str
    source_kind: str
    modality: str
    trust_level: str = FeederSDKTrustLevel.UNTRUSTED
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class FeederSDKEvent:
    """A raw feeder observation before it becomes a validated envelope."""

    source_id: str
    modality: str
    features: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    annotation: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class FeederSDKEnvelope:
    """A validated feeder event, compatible with the plural-sensorium envelope."""

    feeder_id: str
    source_id: str
    source_kind: str
    modality: str
    features: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: f"FSE_{uuid.uuid4().hex[:10]}")
    raw_ref: Optional[str] = None
    annotation: Optional[Any] = None
    annotation_status: str = FeederSDKAnnotationStatus.NONE
    provenance: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    source_mutable_by_solaris: bool = False
    trust_level: str = FeederSDKTrustLevel.UNTRUSTED
    privacy_flags: List[str] = field(default_factory=list)
    contamination_flags: List[str] = field(default_factory=list)
    safety_flags: List[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Structural guarantees: read-only, immutable-by-Solaris, provenance.
        self.read_only = True
        self.source_mutable_by_solaris = False
        if self.modality not in FeederSDKModality.ALL:
            self.modality = FeederSDKModality.UNKNOWN_FIELD
        if self.annotation_status not in FeederSDKAnnotationStatus.ALL:
            self.annotation_status = FeederSDKAnnotationStatus.UNKNOWN
        if self.trust_level not in FeederSDKTrustLevel.ALL:
            self.trust_level = FeederSDKTrustLevel.UNTRUSTED
        self.provenance.setdefault("source_id", self.source_id)
        self.provenance.setdefault("feeder_id", self.feeder_id)
        if self.annotation_status in FeederSDKAnnotationStatus.HUMAN_LABELLED:
            if "human_label_present" not in self.contamination_flags:
                self.contamination_flags.append("human_label_present")
            if "contains_human_text" not in self.privacy_flags:
                self.privacy_flags.append("contains_human_text")
        # Sensory text is observation, never an operator command.
        if "text_is_observation_not_command" not in self.safety_flags:
            self.safety_flags.append("text_is_observation_not_command")

    @property
    def has_provenance(self) -> bool:
        return bool(self.provenance.get("source_id")
                    and self.provenance.get("feeder_id"))

    @property
    def has_human_label(self) -> bool:
        return self.annotation_status in FeederSDKAnnotationStatus.HUMAN_LABELLED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "feeder_id": self.feeder_id,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "modality": self.modality,
            "timestamp": self.timestamp,
            "features": dict(self.features),
            "raw_ref": self.raw_ref,
            "annotation": self.annotation,
            "annotation_status": self.annotation_status,
            "provenance": dict(self.provenance),
            "read_only": True,
            "source_mutable_by_solaris": False,
            "trust_level": self.trust_level,
            "privacy_flags": list(self.privacy_flags),
            "contamination_flags": list(self.contamination_flags),
            "safety_flags": list(self.safety_flags),
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeederSDKEnvelope":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})

    def to_sensory_envelope(self):
        """Map to the Prompt-41 SensoryEventEnvelope the sensorium consumes."""
        from ..plural_sensorium.event_envelope import (
            SensoryEventEnvelope,
            TrustLevel,
        )

        trust_map = {
            FeederSDKTrustLevel.SIMULATED_FIXTURE: TrustLevel.FIXTURE,
            FeederSDKTrustLevel.LOCAL_MANUAL: TrustLevel.MEDIUM,
            FeederSDKTrustLevel.LOCAL_SCRIPT: TrustLevel.MEDIUM,
            FeederSDKTrustLevel.EXTERNAL_FEATURE_ONLY: TrustLevel.LOW,
            FeederSDKTrustLevel.UNVERIFIED_EXTERNAL: TrustLevel.UNTRUSTED,
        }
        prov = dict(self.provenance)
        prov.setdefault("feeder_sdk", True)
        # Privacy flags carry into contamination flags (visible downstream).
        contamination = list(self.contamination_flags)
        for pf in self.privacy_flags:
            if pf not in ("metadata_only", "no_raw_private_content",
                          "contains_rf_features_only"):
                if pf not in contamination:
                    contamination.append(pf)
        return SensoryEventEnvelope(
            source_id=self.source_id, source_kind=self.source_kind,
            modality=self.modality, features=dict(self.features),
            timestamp=self.timestamp, raw_ref=self.raw_ref,
            annotation=self.annotation, annotation_status=self.annotation_status,
            provenance=prov, trust_level=trust_map.get(
                self.trust_level, TrustLevel.UNTRUSTED),
            contamination_flags=contamination,
            metadata={"feeder_id": self.feeder_id,
                      "privacy_flags": list(self.privacy_flags),
                      "safety_flags": list(self.safety_flags),
                      "schema_version": self.schema_version,
                      **dict(self.metadata)})
