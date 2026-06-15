"""Concept birth -- the conservative emergence of proto-concepts from atoms.

The :class:`ConceptBirthEngine` aggregates recurring :class:`PerceptualAtom`s into
:class:`ProtoConcept`s. Birth is conservative: a single isolated event yields at
most a weak/unstable candidate (or nothing), while repeated invariants, recurring
absences, stabilized rhythms, cross-modal recurrences, or metabolic pressure can
support a real candidate. Evidence refs and provenance are always preserved, and
fixture-only vs live-field grounding is recorded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .perceptual_atoms import PerceptualAtom, PerceptualAtomKind
from .proto_concepts import (
    ProtoConcept,
    ProtoConceptGrounding,
    ProtoConceptKind,
    ProtoConceptStatus,
)


class ConceptBirthTrigger:
    REPEATED_INVARIANT = "repeated_invariant"
    RECURRING_ABSENCE = "recurring_absence"
    RHYTHM_STABILIZATION = "rhythm_stabilization"
    CROSS_MODAL_RECURRENCE = "cross_modal_recurrence"
    PREDICTION_IMPROVEMENT = "prediction_improvement"
    COMPRESSION_IMPROVEMENT = "compression_improvement"
    ATTENTION_USEFULNESS = "attention_usefulness"
    REPEATED_SOURCE_HEALTH = "repeated_source_health_pattern"
    METABOLIC_PRESSURE = "perceptual_metabolism_pressure"
    LOGOS_TENSION = "logos_unresolved_tension"
    HYPOTHESIS_SUPPORT = "hypothesis_support"
    CHANGED_PERCEPTION_PROBE = "changed_perception_probe_effect"

    ALL = (REPEATED_INVARIANT, RECURRING_ABSENCE, RHYTHM_STABILIZATION,
           CROSS_MODAL_RECURRENCE, PREDICTION_IMPROVEMENT,
           COMPRESSION_IMPROVEMENT, ATTENTION_USEFULNESS,
           REPEATED_SOURCE_HEALTH, METABOLIC_PRESSURE, LOGOS_TENSION,
           HYPOTHESIS_SUPPORT, CHANGED_PERCEPTION_PROBE)


# Which atom kind maps to which proto-concept kind / grounding.
_ATOM_TO_KIND = {
    PerceptualAtomKind.INVARIANT: (ProtoConceptKind.MODALITY_NATIVE,
                                   ProtoConceptGrounding.FEATURE_GROUNDED),
    PerceptualAtomKind.RHYTHM: (ProtoConceptKind.RHYTHM_BASED,
                                ProtoConceptGrounding.RHYTHM_GROUNDED),
    PerceptualAtomKind.ABSENCE: (ProtoConceptKind.ABSENCE_BASED,
                                 ProtoConceptGrounding.ABSENCE_GROUNDED),
    PerceptualAtomKind.CROSS_MODAL: (ProtoConceptKind.CROSS_MODAL,
                                     ProtoConceptGrounding.CROSS_MODAL_GROUNDED),
    PerceptualAtomKind.SOURCE_HEALTH: (ProtoConceptKind.SOURCE_BASED,
                                       ProtoConceptGrounding.SOURCE_GROUNDED),
    PerceptualAtomKind.OVERLOAD: (ProtoConceptKind.METABOLIC_STATE_BASED,
                                  ProtoConceptGrounding.METABOLIC_GROUNDED),
    PerceptualAtomKind.DEPRIVATION: (ProtoConceptKind.METABOLIC_STATE_BASED,
                                     ProtoConceptGrounding.METABOLIC_GROUNDED),
    PerceptualAtomKind.ATTENTION_SHIFT: (ProtoConceptKind.ATTENTION_BASED,
                                         ProtoConceptGrounding.FEATURE_GROUNDED),
    PerceptualAtomKind.BASELINE_SHIFT: (ProtoConceptKind.BOUNDARY_BASED,
                                        ProtoConceptGrounding.FEATURE_GROUNDED),
    PerceptualAtomKind.FLUX: (ProtoConceptKind.MODALITY_NATIVE,
                              ProtoConceptGrounding.FEATURE_GROUNDED),
    PerceptualAtomKind.HUMAN_ANNOTATION: (
        ProtoConceptKind.HUMAN_LABEL_CONTAMINATED,
        ProtoConceptGrounding.LABEL_GROUNDED),
}

_TRIGGER_FOR_KIND = {
    PerceptualAtomKind.INVARIANT: ConceptBirthTrigger.REPEATED_INVARIANT,
    PerceptualAtomKind.RHYTHM: ConceptBirthTrigger.RHYTHM_STABILIZATION,
    PerceptualAtomKind.ABSENCE: ConceptBirthTrigger.RECURRING_ABSENCE,
    PerceptualAtomKind.CROSS_MODAL: ConceptBirthTrigger.CROSS_MODAL_RECURRENCE,
    PerceptualAtomKind.SOURCE_HEALTH:
        ConceptBirthTrigger.REPEATED_SOURCE_HEALTH,
    PerceptualAtomKind.OVERLOAD: ConceptBirthTrigger.METABOLIC_PRESSURE,
    PerceptualAtomKind.DEPRIVATION: ConceptBirthTrigger.METABOLIC_PRESSURE,
    PerceptualAtomKind.ATTENTION_SHIFT:
        ConceptBirthTrigger.ATTENTION_USEFULNESS,
}


@dataclass
class ConceptBirthCandidate:
    """A proposed concept plus the trigger and evidence that justify it."""

    concept: ProtoConcept
    trigger: str
    weak: bool
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"concept": self.concept.to_dict(), "trigger": self.trigger,
                "weak": self.weak, "evidence_refs": list(self.evidence_refs)}


@dataclass
class ConceptBirthEngine:
    """Aggregates recurring atoms into conservative proto-concept candidates."""

    min_recurrence_for_stable: int = 2
    live_mode: bool = False
    births: int = field(default=0, init=False)

    def propose(self, atoms: List[PerceptualAtom], *,
                metabolism: Optional[Dict[str, Any]] = None,
                priority_boost: float = 0.0) -> List[ConceptBirthCandidate]:
        """Propose concept-birth candidates from the current atoms."""
        candidates: List[ConceptBirthCandidate] = []
        for atom in atoms:
            cand = self._from_atom(atom, priority_boost=priority_boost)
            if cand is not None:
                candidates.append(cand)
        return candidates

    def _from_atom(self, atom: PerceptualAtom,
                   priority_boost: float) -> Optional[ConceptBirthCandidate]:
        kind, grounding = _ATOM_TO_KIND.get(
            atom.kind, (ProtoConceptKind.UNKNOWN,
                        ProtoConceptGrounding.UNGROUNDED))
        weak = not atom.is_recurrent
        # Conservative: a single isolated, non-recurrent, low-novelty atom that
        # carries no metabolic/annotation signal does not justify even a weak
        # candidate.
        if weak and atom.kind in (PerceptualAtomKind.FLUX,
                                  PerceptualAtomKind.UNKNOWN) \
                and atom.novelty < 0.5:
            return None

        status = (ProtoConceptStatus.UNSTABLE if weak
                  else ProtoConceptStatus.EMERGING)
        contamination = 1.0 if atom.human_annotation_external else 0.0
        concept = ProtoConcept(
            kind=kind, status=status, grounding=grounding,
            atom_refs=[atom.atom_id],
            modality_distribution={atom.modality: atom.recurrence_count},
            source_distribution=({atom.source_id: atom.recurrence_count}
                                 if atom.source_id else {}),
            first_seen=atom.timestamp_first_seen,
            last_seen=atom.timestamp_last_seen,
            recurrence_count=atom.recurrence_count,
            stability_score=atom.stability_score,
            grounding_score=(0.0 if atom.human_annotation_external
                             else min(1.0, 0.2 + 0.2 * atom.recurrence_count)),
            prediction_utility=atom.prediction_score,
            compression_utility=atom.compression_score,
            attention_utility=min(1.0, atom.novelty + priority_boost),
            human_label_contamination_score=contamination,
            fixture_grounded=not (self.live_mode and atom.origin == "live_field"),
            live_grounded=(atom.origin == "live_field"),
            provenance_refs=list(atom.provenance_refs) or list(
                atom.sensory_event_refs),
            metadata={"birth_atom_kind": atom.kind,
                      "atom_signature": atom.signature})
        if weak:
            concept.limitations.append(
                "born from a single/low-recurrence observation; weak/unstable")
        if atom.human_annotation_external:
            concept.limitations.append(
                "human-label contaminated; label is external, not ground truth")
        trigger = _TRIGGER_FOR_KIND.get(atom.kind,
                                        ConceptBirthTrigger.REPEATED_INVARIANT)
        self.births += 1
        return ConceptBirthCandidate(
            concept=concept, trigger=trigger, weak=weak,
            evidence_refs=list(concept.provenance_refs))
