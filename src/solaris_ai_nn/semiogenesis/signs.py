"""Internal signs -- compact operational markers, never human words.

An :class:`InternalSign` is an internal marker that helps Solaris compress,
recall, relate, predict, or attend to sensorium-native structures. Its
``sign_code`` is compact and operational (``rf:03a``, ``abs:burst_gap_07``,
``xmod:rf_vib_11``) -- never a human word. A ``human_gloss`` may be attached for
report/debug only; it is never ground truth and never the internal language. Signs
must be grounded in proto-concepts, perceptual atoms, or relations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SignKind:
    MODALITY_NATIVE = "modality_native_sign"
    CROSS_MODAL = "cross_modal_sign"
    ABSENCE = "absence_sign"
    RHYTHM = "rhythm_sign"
    SOURCE = "source_sign"
    BOUNDARY = "boundary_sign"
    INTERFERENCE = "interference_sign"
    METABOLIC = "metabolic_sign"
    ATTENTION = "attention_sign"
    LOGOS_TENSION = "LOGOS_tension_sign"
    HYPOTHESIS = "hypothesis_sign"
    HUMAN_LABEL_CONTAMINATED = "human_label_contaminated_sign"
    UNKNOWN = "unknown_sign"

    ALL = (MODALITY_NATIVE, CROSS_MODAL, ABSENCE, RHYTHM, SOURCE, BOUNDARY,
           INTERFERENCE, METABOLIC, ATTENTION, LOGOS_TENSION, HYPOTHESIS,
           HUMAN_LABEL_CONTAMINATED, UNKNOWN)


class SignStatus:
    CANDIDATE = "candidate"
    EMERGING = "emerging"
    STABLE = "stable"
    AMBIGUOUS = "ambiguous"
    DECAYING = "decaying"
    MERGED = "merged"
    SPLIT = "split"
    REJECTED = "rejected"

    ALL = (CANDIDATE, EMERGING, STABLE, AMBIGUOUS, DECAYING, MERGED, SPLIT,
           REJECTED)


class SignGrounding:
    """How a sign is grounded -- in perceptual structure, never a human label."""

    CONCEPT_GROUNDED = "concept_grounded"
    ATOM_GROUNDED = "atom_grounded"
    RELATION_GROUNDED = "relation_grounded"
    METABOLIC_GROUNDED = "metabolic_grounded"
    LOGOS_GROUNDED = "logos_grounded"
    LABEL_GROUNDED = "label_grounded_external"
    UNGROUNDED = "ungrounded"

    ALL = (CONCEPT_GROUNDED, ATOM_GROUNDED, RELATION_GROUNDED,
           METABOLIC_GROUNDED, LOGOS_GROUNDED, LABEL_GROUNDED, UNGROUNDED)


class GlossStatusMarker:
    """Status markers shared with the gloss layer (re-exported for convenience)."""

    NOT_AVAILABLE = "not_available"
    DEBUG_ONLY = "debug_only"
    APPROXIMATE = "approximate"
    HUMAN_LABEL_CONTAMINATED = "human_label_contaminated"
    OPERATOR_ANNOTATION = "operator_annotation"
    UNSAFE_TO_TRANSLATE = "unsafe_to_translate"


# Compact, operational code prefixes per modality (NOT human words).
_CODE_PREFIX = {
    "radio_frequency": "rf", "alien_rf": "rf",
    "echo": "echo", "alien_echo": "echo",
    "vibration": "vib", "alien_vibration": "vib",
    "magnetic": "mag", "thermal": "therm",
    "machine_rhythm": "mrhythm", "human_textual": "txt",
    "metabolic": "met",
}

_KIND_PREFIX = {
    SignKind.ABSENCE: "abs", SignKind.CROSS_MODAL: "xmod",
    SignKind.SOURCE: "src", SignKind.BOUNDARY: "bnd",
    SignKind.INTERFERENCE: "intf", SignKind.METABOLIC: "met",
    SignKind.ATTENTION: "attn", SignKind.LOGOS_TENSION: "logos",
    SignKind.HYPOTHESIS: "hyp", SignKind.RHYTHM: "rhy",
}

_counter: Dict[str, int] = {}


def _b36(n: int) -> str:
    """A short base-36 suffix so codes stay compact (``03a`` rather than ``39``)."""
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    n = max(0, n)
    while True:
        out = digits[n % 36] + out
        n //= 36
        if n == 0:
            break
    return out.rjust(2, "0")


def operational_sign_code(modality: str, kind: str) -> str:
    """Generate a compact operational sign code (e.g. ``rf:03a``), not a word."""
    prefix = _KIND_PREFIX.get(kind) or _CODE_PREFIX.get(modality) or "sig"
    _counter[prefix] = _counter.get(prefix, 0) + 1
    return f"{prefix}:{_b36(_counter[prefix])}"


@dataclass
class InternalSign:
    """One internal operational sign (a marker, not a human word)."""

    kind: str
    sign_id: str = field(default_factory=lambda: f"SIGN_{uuid.uuid4().hex[:8]}")
    sign_code: str = ""
    status: str = SignStatus.CANDIDATE
    grounding: str = SignGrounding.CONCEPT_GROUNDED
    proto_concept_refs: List[str] = field(default_factory=list)
    perceptual_atom_refs: List[str] = field(default_factory=list)
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    source_distribution: Dict[str, int] = field(default_factory=dict)
    first_seen: float = 0.0
    last_seen: float = 0.0
    recurrence_count: int = 1
    grounding_score: float = 0.0
    compression_utility: float = 0.0
    prediction_utility: float = 0.0
    attention_utility: float = 0.0
    relation_utility: float = 0.0
    ambiguity_score: float = 0.0
    contamination_flags: List[str] = field(default_factory=list)
    human_gloss: Optional[str] = None
    human_gloss_status: str = GlossStatusMarker.NOT_AVAILABLE
    provenance_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sign_code:
            modality = (max(self.modality_distribution,
                            key=self.modality_distribution.get)
                        if self.modality_distribution else "unknown")
            self.sign_code = operational_sign_code(modality, self.kind)
        if not self.limitations:
            self.limitations = [
                "operational marker for compression/prediction/attention/"
                "relation, not a human word",
                "any human gloss is an approximate debug annotation, not ground "
                "truth",
            ]

    @property
    def dominant_modality(self) -> Optional[str]:
        if not self.modality_distribution:
            return None
        return max(self.modality_distribution,
                   key=self.modality_distribution.get)

    @property
    def is_contaminated(self) -> bool:
        return (self.kind == SignKind.HUMAN_LABEL_CONTAMINATED
                or bool(self.contamination_flags))

    @property
    def is_cross_modal(self) -> bool:
        return (self.kind == SignKind.CROSS_MODAL
                or len(self.modality_distribution) > 1)

    @property
    def is_absence(self) -> bool:
        return self.kind == SignKind.ABSENCE

    @property
    def is_ambiguous(self) -> bool:
        return self.status == SignStatus.AMBIGUOUS or self.ambiguity_score >= 0.5

    def utility(self) -> float:
        return round((self.compression_utility + self.prediction_utility
                      + self.attention_utility + self.relation_utility) / 4.0, 4)

    def attach_gloss(self, gloss: str, status: str) -> None:
        """Attach a human-readable gloss (debug/report only; never ground truth)."""
        self.human_gloss = str(gloss)
        self.human_gloss_status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id,
            "sign_code": self.sign_code,
            "kind": self.kind,
            "status": self.status,
            "grounding": self.grounding,
            "proto_concept_refs": list(self.proto_concept_refs),
            "perceptual_atom_refs": list(self.perceptual_atom_refs),
            "modality_distribution": dict(self.modality_distribution),
            "source_distribution": dict(self.source_distribution),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "recurrence_count": self.recurrence_count,
            "grounding_score": round(self.grounding_score, 4),
            "compression_utility": round(self.compression_utility, 4),
            "prediction_utility": round(self.prediction_utility, 4),
            "attention_utility": round(self.attention_utility, 4),
            "relation_utility": round(self.relation_utility, 4),
            "utility": self.utility(),
            "ambiguity_score": round(self.ambiguity_score, 4),
            "contamination_flags": list(self.contamination_flags),
            "human_gloss": self.human_gloss,
            "human_gloss_status": self.human_gloss_status,
            "is_cross_modal": self.is_cross_modal,
            "is_absence": self.is_absence,
            "is_contaminated": self.is_contaminated,
            "provenance_refs": list(self.provenance_refs),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "note": "internal operational sign, not a human word or proof of "
                    "language understanding",
        }
