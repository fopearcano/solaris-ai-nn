"""Proto-concepts -- stabilized internal structures, not words or categories.

A :class:`ProtoConcept` is a sensorium-native structure that helps Solaris
compress, predict, relate to, or respond to its sensorium. It is NOT a word, NOT a
human category (person/object/room/dog/sentence), and never requires a name. If a
display name is needed, a neutral operational one (e.g. ``rf_pattern_003``) is
generated -- never a human semantic label. Human labels may be attached only as
external annotations, and grounding depends on repeated feature evidence, never on
semantic labels.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ProtoConceptKind:
    MODALITY_NATIVE = "modality_native"
    CROSS_MODAL = "cross_modal"
    ABSENCE_BASED = "absence_based"
    RHYTHM_BASED = "rhythm_based"
    SOURCE_BASED = "source_based"
    BOUNDARY_BASED = "boundary_based"
    INTERFERENCE_BASED = "interference_based"
    METABOLIC_STATE_BASED = "metabolic_state_based"
    ATTENTION_BASED = "attention_based"
    HUMAN_LABEL_CONTAMINATED = "human_label_contaminated"
    UNKNOWN = "unknown"

    ALL = (MODALITY_NATIVE, CROSS_MODAL, ABSENCE_BASED, RHYTHM_BASED,
           SOURCE_BASED, BOUNDARY_BASED, INTERFERENCE_BASED,
           METABOLIC_STATE_BASED, ATTENTION_BASED, HUMAN_LABEL_CONTAMINATED,
           UNKNOWN)


class ProtoConceptStatus:
    CANDIDATE = "candidate"
    EMERGING = "emerging"
    STABLE = "stable"
    UNSTABLE = "unstable"
    DECAYING = "decaying"
    MERGED = "merged"
    SPLIT = "split"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"

    ALL = (CANDIDATE, EMERGING, STABLE, UNSTABLE, DECAYING, MERGED, SPLIT,
           REJECTED, AMBIGUOUS)


class ProtoConceptGrounding:
    """How a concept is grounded -- feature evidence, never a semantic label."""

    FEATURE_GROUNDED = "feature_grounded"
    RHYTHM_GROUNDED = "rhythm_grounded"
    ABSENCE_GROUNDED = "absence_grounded"
    CROSS_MODAL_GROUNDED = "cross_modal_grounded"
    SOURCE_GROUNDED = "source_grounded"
    METABOLIC_GROUNDED = "metabolic_grounded"
    LABEL_GROUNDED = "label_grounded_external"
    UNGROUNDED = "ungrounded"

    ALL = (FEATURE_GROUNDED, RHYTHM_GROUNDED, ABSENCE_GROUNDED,
           CROSS_MODAL_GROUNDED, SOURCE_GROUNDED, METABOLIC_GROUNDED,
           LABEL_GROUNDED, UNGROUNDED)


# Neutral operational name prefixes per modality family (NOT human semantics).
_NAME_PREFIX = {
    "radio_frequency": "rf_pattern",
    "alien_rf": "rf_pattern",
    "echo": "echo_pattern",
    "alien_echo": "echo_pattern",
    "vibration": "vib_pattern",
    "alien_vibration": "vib_pattern",
    "magnetic": "mag_pattern",
    "thermal": "therm_pattern",
    "machine_rhythm": "rhythm_pattern",
    "human_textual": "text_pattern",
}

_counter: Dict[str, int] = {}


def neutral_operational_name(modality: str, kind: str) -> str:
    """Generate a neutral operational name like ``rf_pattern_003`` (not a word)."""
    prefix = _NAME_PREFIX.get(modality)
    if prefix is None:
        if kind == ProtoConceptKind.ABSENCE_BASED:
            prefix = "absence_pattern"
        elif kind == ProtoConceptKind.CROSS_MODAL:
            prefix = "xmodal_pattern"
        elif kind == ProtoConceptKind.METABOLIC_STATE_BASED:
            prefix = "metabolic_pattern"
        else:
            prefix = "pattern"
    _counter[prefix] = _counter.get(prefix, 0) + 1
    return f"{prefix}_{_counter[prefix]:03d}"


@dataclass
class ProtoConcept:
    """One sensorium-native proto-concept (operational structure, not a word)."""

    kind: str
    concept_id: str = field(
        default_factory=lambda: f"CONCEPT_{uuid.uuid4().hex[:8]}")
    status: str = ProtoConceptStatus.CANDIDATE
    grounding: str = ProtoConceptGrounding.FEATURE_GROUNDED
    operational_name: str = ""
    atom_refs: List[str] = field(default_factory=list)
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    source_distribution: Dict[str, int] = field(default_factory=dict)
    first_seen: float = 0.0
    last_seen: float = 0.0
    recurrence_count: int = 1
    stability_score: float = 0.0
    grounding_score: float = 0.0
    prediction_utility: float = 0.0
    compression_utility: float = 0.0
    attention_utility: float = 0.0
    relation_count: int = 0
    parent_concepts: List[str] = field(default_factory=list)
    child_concepts: List[str] = field(default_factory=list)
    human_label_contamination_score: float = 0.0
    fixture_grounded: bool = True
    live_grounded: bool = False
    human_annotations: List[str] = field(default_factory=list)
    provenance_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.operational_name:
            modality = (max(self.modality_distribution,
                            key=self.modality_distribution.get)
                        if self.modality_distribution else "unknown")
            self.operational_name = neutral_operational_name(modality, self.kind)
        if not self.limitations:
            self.limitations = [
                "operational structure for compression/prediction/relation, "
                "not a word or a human category",
                "stability is provisional; stable does not mean true",
            ]

    @property
    def dominant_modality(self) -> Optional[str]:
        if not self.modality_distribution:
            return None
        return max(self.modality_distribution,
                   key=self.modality_distribution.get)

    @property
    def is_contaminated(self) -> bool:
        return (self.kind == ProtoConceptKind.HUMAN_LABEL_CONTAMINATED
                or self.human_label_contamination_score >= 0.5)

    @property
    def is_cross_modal(self) -> bool:
        return len(self.modality_distribution) > 1

    @property
    def is_absence_based(self) -> bool:
        return self.kind == ProtoConceptKind.ABSENCE_BASED

    def attach_human_annotation(self, annotation: str) -> None:
        """Attach a human label as an external annotation only (not ground truth)."""
        self.human_annotations.append(str(annotation))
        self.human_label_contamination_score = min(
            1.0, self.human_label_contamination_score + 0.25)

    def utility(self) -> float:
        return round((self.prediction_utility + self.compression_utility
                      + self.attention_utility) / 3.0, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "kind": self.kind,
            "status": self.status,
            "grounding": self.grounding,
            "operational_name": self.operational_name,
            "atom_refs": list(self.atom_refs),
            "modality_distribution": dict(self.modality_distribution),
            "source_distribution": dict(self.source_distribution),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "recurrence_count": self.recurrence_count,
            "stability_score": round(self.stability_score, 4),
            "grounding_score": round(self.grounding_score, 4),
            "prediction_utility": round(self.prediction_utility, 4),
            "compression_utility": round(self.compression_utility, 4),
            "attention_utility": round(self.attention_utility, 4),
            "utility": self.utility(),
            "relation_count": self.relation_count,
            "parent_concepts": list(self.parent_concepts),
            "child_concepts": list(self.child_concepts),
            "human_label_contamination_score": round(
                self.human_label_contamination_score, 4),
            "fixture_grounded": self.fixture_grounded,
            "live_grounded": self.live_grounded,
            "human_annotations": list(self.human_annotations),
            "is_cross_modal": self.is_cross_modal,
            "is_absence_based": self.is_absence_based,
            "is_contaminated": self.is_contaminated,
            "provenance_refs": list(self.provenance_refs),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "note": "proto-concept: an operational internal structure, not a "
                    "word, a human category, or proof of understanding",
        }
