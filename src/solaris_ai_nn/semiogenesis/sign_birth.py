"""Sign birth -- the conservative emergence of internal signs from concepts.

The :class:`SignBirthEngine` turns stable/useful proto-concepts (and their
relations) into :class:`InternalSign`s. Birth is conservative: not every event or
concept earns a sign, isolated noise earns none, signs born only from human labels
are marked contaminated, and fixture-vs-live grounding is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .signs import InternalSign, SignGrounding, SignKind, SignStatus


class SignBirthTrigger:
    STABLE_PROTO_CONCEPT = "stable_proto_concept"
    REPEATED_CROSS_MODAL = "repeated_cross_modal_relation"
    HIGH_COMPRESSION = "high_compression_utility"
    PREDICTION_UTILITY = "prediction_utility"
    ATTENTION_UTILITY = "attention_utility"
    REPEATED_ABSENCE = "repeated_absence_structure"
    STABLE_FAMILY = "stable_concept_family"
    LOGOS_TENSION_MARKER = "unresolved_logos_tension_marker"
    HYPOTHESIS_RECURRENT = "hypothesis_recurrently_used"
    METABOLIC_RECURRENCE = "metabolic_state_recurrence"
    REPORT_REFERENCE_NEED = "operator_report_reference_need"

    ALL = (STABLE_PROTO_CONCEPT, REPEATED_CROSS_MODAL, HIGH_COMPRESSION,
           PREDICTION_UTILITY, ATTENTION_UTILITY, REPEATED_ABSENCE,
           STABLE_FAMILY, LOGOS_TENSION_MARKER, HYPOTHESIS_RECURRENT,
           METABOLIC_RECURRENCE, REPORT_REFERENCE_NEED)


# Map a proto-concept kind onto a sign kind / grounding.
_CONCEPT_TO_SIGN = {
    "modality_native": (SignKind.MODALITY_NATIVE, SignGrounding.CONCEPT_GROUNDED),
    "cross_modal": (SignKind.CROSS_MODAL, SignGrounding.RELATION_GROUNDED),
    "absence_based": (SignKind.ABSENCE, SignGrounding.CONCEPT_GROUNDED),
    "rhythm_based": (SignKind.RHYTHM, SignGrounding.CONCEPT_GROUNDED),
    "source_based": (SignKind.SOURCE, SignGrounding.CONCEPT_GROUNDED),
    "boundary_based": (SignKind.BOUNDARY, SignGrounding.CONCEPT_GROUNDED),
    "interference_based": (SignKind.INTERFERENCE,
                           SignGrounding.CONCEPT_GROUNDED),
    "metabolic_state_based": (SignKind.METABOLIC,
                              SignGrounding.METABOLIC_GROUNDED),
    "attention_based": (SignKind.ATTENTION, SignGrounding.CONCEPT_GROUNDED),
    "human_label_contaminated": (SignKind.HUMAN_LABEL_CONTAMINATED,
                                 SignGrounding.LABEL_GROUNDED),
    "unknown": (SignKind.UNKNOWN, SignGrounding.UNGROUNDED),
}


@dataclass
class SignBirthCandidate:
    """A proposed sign plus the trigger and evidence that justify it."""

    sign: InternalSign
    trigger: str
    weak: bool
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"sign": self.sign.to_dict(), "trigger": self.trigger,
                "weak": self.weak, "evidence_refs": list(self.evidence_refs)}


@dataclass
class SignBirthEngine:
    """Conservatively turns useful proto-concepts into internal signs."""

    min_stability_for_sign: float = 0.3
    live_mode: bool = False
    births: int = field(default=0, init=False)

    def propose(self, concepts: List[Any], *,
                priority_boost: float = 0.0) -> List[SignBirthCandidate]:
        """Propose sign-birth candidates from concepts worth a stable reference."""
        candidates: List[SignBirthCandidate] = []
        for concept in concepts:
            cand = self._from_concept(concept, priority_boost=priority_boost)
            if cand is not None:
                candidates.append(cand)
        return candidates

    def _from_concept(self, concept: Any,
                      priority_boost: float) -> Optional[SignBirthCandidate]:
        status = getattr(concept, "status", "candidate")
        contaminated = bool(getattr(concept, "is_contaminated", False))
        stability = float(getattr(concept, "stability_score", 0.0))
        recurrence = int(getattr(concept, "recurrence_count", 1))
        utility = max(float(getattr(concept, "prediction_utility", 0.0)),
                      float(getattr(concept, "compression_utility", 0.0)),
                      float(getattr(concept, "attention_utility", 0.0)))

        # Conservative: isolated noise (single low-stability, low-utility,
        # non-contaminated concept) earns no sign at all.
        if (status in ("candidate", "unstable") and recurrence <= 1
                and stability < self.min_stability_for_sign
                and utility < 0.3 and not contaminated):
            return None

        weak = status in ("candidate", "unstable", "ambiguous")
        kind, grounding = _CONCEPT_TO_SIGN.get(
            getattr(concept, "kind", "unknown"),
            (SignKind.UNKNOWN, SignGrounding.UNGROUNDED))

        sign = InternalSign(
            kind=kind, grounding=grounding,
            status=(SignStatus.EMERGING if weak else SignStatus.STABLE),
            proto_concept_refs=[getattr(concept, "concept_id", "")],
            perceptual_atom_refs=list(getattr(concept, "atom_refs", [])),
            modality_distribution=dict(
                getattr(concept, "modality_distribution", {})),
            source_distribution=dict(
                getattr(concept, "source_distribution", {})),
            first_seen=float(getattr(concept, "first_seen", 0.0)),
            last_seen=float(getattr(concept, "last_seen", 0.0)),
            recurrence_count=recurrence,
            grounding_score=(0.0 if contaminated
                             else float(getattr(concept, "grounding_score",
                                                0.0))),
            compression_utility=float(getattr(concept, "compression_utility",
                                              0.0)),
            prediction_utility=float(getattr(concept, "prediction_utility",
                                            0.0)),
            attention_utility=min(1.0, float(getattr(
                concept, "attention_utility", 0.0)) + priority_boost),
            relation_utility=min(1.0, 0.2 * int(getattr(
                concept, "relation_count", 0))),
            ambiguity_score=(0.6 if status == "ambiguous" else 0.0),
            contamination_flags=(["concept_human_label_contaminated"]
                                 if contaminated else []),
            provenance_refs=list(getattr(concept, "provenance_refs", [])),
            metadata={"birth_concept_kind": getattr(concept, "kind", "unknown"),
                      "concept_operational_name":
                      getattr(concept, "operational_name", "")})
        sign.metadata["concept_signature"] = getattr(
            concept, "concept_id", sign.sign_id)
        if weak:
            sign.limitations.append(
                "born from a weak/unstable/ambiguous concept; provisional")
        if contaminated:
            sign.limitations.append(
                "human-label contaminated; gloss/label is external, not ground "
                "truth")

        trigger = (SignBirthTrigger.STABLE_PROTO_CONCEPT if status == "stable"
                   else SignBirthTrigger.REPEATED_CROSS_MODAL
                   if kind == SignKind.CROSS_MODAL
                   else SignBirthTrigger.REPEATED_ABSENCE
                   if kind == SignKind.ABSENCE
                   else SignBirthTrigger.METABOLIC_RECURRENCE
                   if kind == SignKind.METABOLIC
                   else SignBirthTrigger.HIGH_COMPRESSION)
        self.births += 1
        return SignBirthCandidate(sign=sign, trigger=trigger, weak=weak,
                                  evidence_refs=list(sign.provenance_refs))
