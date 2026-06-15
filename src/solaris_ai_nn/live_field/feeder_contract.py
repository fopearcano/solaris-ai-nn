"""Live feeder contract -- the data shape real external feeders must produce.

A live feeder is a *separate* process the operator runs; it writes
:class:`LiveFeederEnvelope` records (JSONL) into local files. Solaris reads those
files read-only and never controls the feeder. The envelope is compatible with the
Prompt-41 :class:`SensoryEventEnvelope`: features are primary, human annotations
are optional and never ground truth, sensory text is never a command, and
provenance is mandatory.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..plural_sensorium.event_envelope import AnnotationStatus, SensoryEventEnvelope
from ..plural_sensorium.modality import ModalityFamily, family_for_hint


class LiveFeederMode:
    MANUAL = "manual"
    LOCAL_FILE = "local_file"
    LOCAL_FOLDER = "local_folder"
    LOCAL_SYSTEM_RHYTHM = "local_system_rhythm"
    EXTERNAL_FEATURE_DROP = "external_feature_drop"
    EXTERNAL_SENSOR_EXPORT = "external_sensor_export"
    FIXTURE_REPLAY = "fixture_replay"
    UNKNOWN = "unknown"

    ALL = (MANUAL, LOCAL_FILE, LOCAL_FOLDER, LOCAL_SYSTEM_RHYTHM,
           EXTERNAL_FEATURE_DROP, EXTERNAL_SENSOR_EXPORT, FIXTURE_REPLAY,
           UNKNOWN)
    # Modes that describe a real outside-world source (need governance to read).
    REAL_WORLD = frozenset({EXTERNAL_SENSOR_EXPORT})


class LiveFeederTrust:
    TRUSTED_LOCAL_MANUAL = "trusted_local_manual"
    TRUSTED_LOCAL_SCRIPT = "trusted_local_script"
    EXTERNAL_FEATURE_ONLY = "external_feature_only"
    UNVERIFIED_EXTERNAL = "unverified_external"
    FIXTURE = "fixture"
    UNKNOWN = "unknown"

    ALL = (TRUSTED_LOCAL_MANUAL, TRUSTED_LOCAL_SCRIPT, EXTERNAL_FEATURE_ONLY,
           UNVERIFIED_EXTERNAL, FIXTURE, UNKNOWN)


@dataclass
class LiveFeederEvent:
    """A raw feeder observation before it becomes a validated envelope."""

    source_id: str
    modality: str
    features: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    annotation: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LiveFeederEnvelope:
    """A validated live event, compatible with the plural-sensorium envelope."""

    source_id: str
    feeder_id: str
    feeder_mode: str
    modality: str
    features: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: f"LFE_{uuid.uuid4().hex[:10]}")
    raw_ref: Optional[str] = None
    annotation: Optional[Any] = None
    annotation_status: str = AnnotationStatus.NONE
    provenance: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    source_mutable_by_solaris: bool = False
    trust_level: str = LiveFeederTrust.UNKNOWN
    contamination_flags: List[str] = field(default_factory=list)
    safety_flags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Structural guarantees: read-only, immutable-by-Solaris, provenance.
        self.read_only = True
        self.source_mutable_by_solaris = False
        if self.feeder_mode not in LiveFeederMode.ALL:
            self.feeder_mode = LiveFeederMode.UNKNOWN
        if self.trust_level not in LiveFeederTrust.ALL:
            self.trust_level = LiveFeederTrust.UNKNOWN
        if self.annotation_status not in AnnotationStatus.ALL:
            self.annotation_status = AnnotationStatus.UNKNOWN
        self.provenance.setdefault("source_id", self.source_id)
        self.provenance.setdefault("feeder_id", self.feeder_id)
        self.provenance.setdefault("feeder_mode", self.feeder_mode)
        if self.annotation_status in AnnotationStatus.HUMAN_LABELLED \
                and "human_label_present" not in self.contamination_flags:
            self.contamination_flags.append("human_label_present")

    @property
    def has_provenance(self) -> bool:
        return bool(self.provenance.get("source_id")
                    and self.provenance.get("feeder_id"))

    @property
    def has_human_label(self) -> bool:
        return self.annotation_status in AnnotationStatus.HUMAN_LABELLED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source_id": self.source_id,
            "feeder_id": self.feeder_id,
            "feeder_mode": self.feeder_mode,
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
            "contamination_flags": list(self.contamination_flags),
            "safety_flags": list(self.safety_flags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LiveFeederEnvelope":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})

    def to_sensory_envelope(self) -> SensoryEventEnvelope:
        """Convert to the Prompt-41 envelope the plural sensorium consumes."""
        prov = dict(self.provenance)
        prov.setdefault("live_feeder", True)
        return SensoryEventEnvelope(
            source_id=self.source_id, source_kind=self.feeder_mode,
            modality=self.modality, features=dict(self.features),
            timestamp=self.timestamp, raw_ref=self.raw_ref,
            annotation=self.annotation, annotation_status=self.annotation_status,
            provenance=prov, trust_level=self._sensory_trust(),
            contamination_flags=list(self.contamination_flags),
            metadata={"feeder_id": self.feeder_id,
                      "safety_flags": list(self.safety_flags),
                      **dict(self.metadata)})

    def _sensory_trust(self) -> str:
        from ..plural_sensorium.event_envelope import TrustLevel

        return {
            LiveFeederTrust.FIXTURE: TrustLevel.FIXTURE,
            LiveFeederTrust.TRUSTED_LOCAL_MANUAL: TrustLevel.MEDIUM,
            LiveFeederTrust.TRUSTED_LOCAL_SCRIPT: TrustLevel.MEDIUM,
            LiveFeederTrust.EXTERNAL_FEATURE_ONLY: TrustLevel.LOW,
            LiveFeederTrust.UNVERIFIED_EXTERNAL: TrustLevel.UNTRUSTED,
        }.get(self.trust_level, TrustLevel.UNTRUSTED)


@dataclass
class LiveFeederContract:
    """Validates raw feeder records and builds live envelopes (read-only)."""

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        if not isinstance(record, dict):
            return False, ["record is not an object"]
        # Note: modality may be supplied by the feeder/inbox hint rather than the
        # record itself, so its absence here is not a rejection -- but there must
        # be some content (features / numeric values / an annotation).
        features = record.get("features")
        explicit = isinstance(features, dict)
        numeric = any(isinstance(v, (int, float)) for k, v in record.items()
                      if k not in ("ts", "timestamp"))
        if not explicit and not numeric and not record.get("annotation"):
            reasons.append("no features (numeric content is primary)")
        ts = record.get("timestamp", record.get("ts"))
        if ts is not None:
            try:
                float(ts)
            except (TypeError, ValueError):
                reasons.append("invalid timestamp")
        # An "executable" payload is never accepted as a feature.
        if any(k in record for k in ("__exec__", "command", "shell", "eval")):
            reasons.append("executable/command payloads are rejected")
        return (not reasons), reasons

    def build_envelope(self, record: Dict[str, Any], *, feeder_id: str,
                       feeder_mode: str, source_id: str, modality_hint: str = "",
                       trust_level: str = LiveFeederTrust.UNKNOWN,
                       raw_ref: Optional[str] = None) -> LiveFeederEnvelope:
        modality = self._modality(record, modality_hint)
        features = self._features(record)
        annotation = record.get("annotation", record.get("label"))
        status = record.get("annotation_status")
        if status not in AnnotationStatus.ALL:
            status = (AnnotationStatus.EXTERNAL_NON_GROUND_TRUTH
                      if annotation is not None else AnnotationStatus.NONE)
        ts = record.get("timestamp", record.get("ts"))
        return LiveFeederEnvelope(
            source_id=source_id or str(record.get("source_id", feeder_id)),
            feeder_id=feeder_id, feeder_mode=feeder_mode, modality=modality,
            features=features, timestamp=float(ts) if ts is not None
            else time.time(), raw_ref=raw_ref, annotation=annotation,
            annotation_status=status, trust_level=trust_level,
            provenance={"source_id": source_id or feeder_id,
                        "feeder_id": feeder_id, "feeder_mode": feeder_mode,
                        "raw_ref": raw_ref})

    @staticmethod
    def _modality(record: Dict[str, Any], hint: str) -> str:
        mod = record.get("modality")
        if mod:
            fam = family_for_hint(str(mod))
            return fam if fam != ModalityFamily.UNKNOWN_FIELD else str(mod)
        return family_for_hint(hint)

    @staticmethod
    def _features(record: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(record.get("features"), dict):
            return dict(record["features"])
        skip = {"modality", "annotation", "label", "annotation_status",
                "timestamp", "ts", "source_id"}
        return {k: v for k, v in record.items() if k not in skip}
