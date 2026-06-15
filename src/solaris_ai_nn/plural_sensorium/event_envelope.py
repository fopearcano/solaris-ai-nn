"""Sensory Event Envelope -- the common outside-event contract.

Every incoming event becomes a :class:`SensoryEventEnvelope`. The numeric/feature
content is *primary*; any human annotation is *secondary* and never ground truth
by default. Provenance is always preserved, the source is read-only and not
mutable by Solaris, and sensory text is never an operator command.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AnnotationStatus:
    NONE = "none"
    EXTERNAL_NON_GROUND_TRUTH = "external_non_ground_truth"
    HUMAN_LABEL_EXTERNAL = "human_label_external"
    GENERATED_BY_FEEDER = "generated_by_feeder"
    UNKNOWN = "unknown"

    ALL = (NONE, EXTERNAL_NON_GROUND_TRUTH, HUMAN_LABEL_EXTERNAL,
           GENERATED_BY_FEEDER, UNKNOWN)
    # Annotation statuses that carry a human-supplied label (contamination risk).
    HUMAN_LABELLED = frozenset({HUMAN_LABEL_EXTERNAL})


class TrustLevel:
    UNTRUSTED = "untrusted"
    FIXTURE = "fixture"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    ALL = (UNTRUSTED, FIXTURE, LOW, MEDIUM, HIGH)


@dataclass
class SensoryEventEnvelope:
    """One normalized outside-world event. Features primary; labels secondary."""

    source_id: str
    source_kind: str
    modality: str
    features: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: f"SEV_{uuid.uuid4().hex[:10]}")
    raw_ref: Optional[str] = None
    annotation: Optional[Any] = None
    annotation_status: str = AnnotationStatus.NONE
    provenance: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    source_mutable_by_solaris: bool = False
    trust_level: str = TrustLevel.FIXTURE
    contamination_flags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Read-only and immutable-by-Solaris are structural guarantees.
        self.read_only = True
        self.source_mutable_by_solaris = False
        if self.annotation_status not in AnnotationStatus.ALL:
            self.annotation_status = AnnotationStatus.UNKNOWN
        if self.trust_level not in TrustLevel.ALL:
            self.trust_level = TrustLevel.UNTRUSTED
        # A human label is never ground truth; flag it as a contamination risk.
        if self.annotation_status in AnnotationStatus.HUMAN_LABELLED \
                and "human_label_present" not in self.contamination_flags:
            self.contamination_flags.append("human_label_present")
        # Provenance must always be present.
        self.provenance.setdefault("source_id", self.source_id)
        self.provenance.setdefault("source_kind", self.source_kind)

    @property
    def has_human_label(self) -> bool:
        return self.annotation_status in AnnotationStatus.HUMAN_LABELLED

    @property
    def has_provenance(self) -> bool:
        return bool(self.provenance.get("source_id"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
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
            "contamination_flags": list(self.contamination_flags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SensoryEventEnvelope":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
