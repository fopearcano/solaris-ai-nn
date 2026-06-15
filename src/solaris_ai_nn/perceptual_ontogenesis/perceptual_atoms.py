"""Perceptual atoms -- the proto-material from which concepts are later born.

A :class:`PerceptualAtom` is a single recurring perceptual structure extracted
from the sensorium (a flux burst, an absence, a rhythm, an invariant, a cross-modal
disturbance, a receptor/source-health state, a baseline/attention shift, an
overload/deprivation signal, or an external human annotation). Atoms are NOT
concepts; they are raw, provenance-bearing observations that the
:class:`ConceptBirthEngine` later aggregates. Human annotations may create atoms,
but those atoms are always marked external / non-ground-truth.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class PerceptualAtomKind:
    FLUX = "flux_atom"
    ABSENCE = "absence_atom"
    RHYTHM = "rhythm_atom"
    INVARIANT = "invariant_atom"
    CROSS_MODAL = "cross_modal_atom"
    RECEPTOR_STATE = "receptor_state_atom"
    BASELINE_SHIFT = "baseline_shift_atom"
    ATTENTION_SHIFT = "attention_shift_atom"
    OVERLOAD = "overload_atom"
    DEPRIVATION = "deprivation_atom"
    SOURCE_HEALTH = "source_health_atom"
    HUMAN_ANNOTATION = "human_annotation_atom"
    UNKNOWN = "unknown_atom"

    ALL = (FLUX, ABSENCE, RHYTHM, INVARIANT, CROSS_MODAL, RECEPTOR_STATE,
           BASELINE_SHIFT, ATTENTION_SHIFT, OVERLOAD, DEPRIVATION,
           SOURCE_HEALTH, HUMAN_ANNOTATION, UNKNOWN)


class PerceptualAtomSource:
    """Where an atom came from (never ground truth if human-annotated)."""

    FIXTURE = "fixture"
    LIVE_FIELD = "live_field"
    FEEDER_SDK = "feeder_sdk"
    METABOLISM = "perceptual_metabolism"
    HUMAN_ANNOTATION = "human_annotation_external"

    ALL = (FIXTURE, LIVE_FIELD, FEEDER_SDK, METABOLISM, HUMAN_ANNOTATION)


@dataclass
class PerceptualAtom:
    """One provenance-bearing perceptual structure (proto-material, not concept)."""

    kind: str
    modality: str = "unknown"
    source_id: str = ""
    atom_id: str = field(default_factory=lambda: f"ATOM_{uuid.uuid4().hex[:8]}")
    receptor_id: str = ""
    sensory_event_refs: List[str] = field(default_factory=list)
    trace_refs: List[str] = field(default_factory=list)
    timestamp_first_seen: float = 0.0
    timestamp_last_seen: float = 0.0
    intensity: float = 0.0
    novelty: float = 0.0
    recurrence_count: int = 1
    stability_score: float = 0.0
    prediction_score: float = 0.0
    compression_score: float = 0.0
    contamination_flags: List[str] = field(default_factory=list)
    provenance_refs: List[str] = field(default_factory=list)
    origin: str = PerceptualAtomSource.FIXTURE
    human_annotation_external: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Human-annotation atoms are always external / non-ground-truth.
        if self.kind == PerceptualAtomKind.HUMAN_ANNOTATION:
            self.human_annotation_external = True
            self.origin = PerceptualAtomSource.HUMAN_ANNOTATION
            if "human_label_external" not in self.contamination_flags:
                self.contamination_flags.append("human_label_external")

    @property
    def signature(self) -> str:
        """A stable structural key used to merge recurring atoms."""
        base = self.metadata.get("signature")
        if base:
            return str(base)
        return f"{self.kind}:{self.modality}:{self.source_id}"

    def observe_again(self, timestamp: float = 0.0) -> None:
        self.recurrence_count += 1
        if timestamp:
            self.timestamp_last_seen = max(self.timestamp_last_seen, timestamp)
        # Recurrence nudges stability (bounded).
        self.stability_score = min(1.0, self.stability_score + 0.1)

    @property
    def is_recurrent(self) -> bool:
        return self.recurrence_count >= 2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "kind": self.kind,
            "modality": self.modality,
            "source_id": self.source_id,
            "receptor_id": self.receptor_id,
            "sensory_event_refs": list(self.sensory_event_refs),
            "trace_refs": list(self.trace_refs),
            "timestamp_first_seen": self.timestamp_first_seen,
            "timestamp_last_seen": self.timestamp_last_seen,
            "intensity": round(self.intensity, 4),
            "novelty": round(self.novelty, 4),
            "recurrence_count": self.recurrence_count,
            "stability_score": round(self.stability_score, 4),
            "prediction_score": round(self.prediction_score, 4),
            "compression_score": round(self.compression_score, 4),
            "contamination_flags": list(self.contamination_flags),
            "provenance_refs": list(self.provenance_refs),
            "origin": self.origin,
            "human_annotation_external": self.human_annotation_external,
            "signature": self.signature,
            "metadata": dict(self.metadata),
            "note": "proto-material for concepts, not a concept or a word",
        }


@dataclass
class PerceptualAtomTrace:
    """An append-only-style record of how an atom changed over observations."""

    atom_id: str
    observations: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, snapshot: Dict[str, Any]) -> None:
        self.observations.append(dict(snapshot))

    def to_dict(self) -> Dict[str, Any]:
        return {"atom_id": self.atom_id,
                "observation_count": len(self.observations),
                "observations": list(self.observations)}
