"""Decay -- recording when concepts stop earning their keep (without deleting).

The :class:`ConceptDecayEngine` records why a proto-concept is decaying, rejected,
merged, or split. Decay never deletes evidence: a decayed concept remains
historically visible as a new state record, and decay is treated as part of
learning, not failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .proto_concepts import ProtoConcept, ProtoConceptStatus


class DecayReason:
    NOT_SEEN_AGAIN = "not_seen_again"
    PREDICTION_FAILED = "prediction_failed"
    COMPRESSION_USELESS = "compression_useless"
    ATTENTION_USELESS = "attention_useless"
    CONTRADICTED = "contradicted_by_later_evidence"
    OVERFIT_FIXTURE = "overfit_to_fixture"
    SOURCE_CORRUPTED = "source_corrupted"
    LABEL_CONTAMINATION = "human_label_contamination"
    FALSE_PATTERN = "false_pattern"
    MERGED = "merged_into_stronger_concept"
    SPLIT = "split_into_sub_concepts"

    ALL = (NOT_SEEN_AGAIN, PREDICTION_FAILED, COMPRESSION_USELESS,
           ATTENTION_USELESS, CONTRADICTED, OVERFIT_FIXTURE, SOURCE_CORRUPTED,
           LABEL_CONTAMINATION, FALSE_PATTERN, MERGED, SPLIT)


@dataclass
class DecayResult:
    concept_id: str
    decayed: bool
    new_status: str
    reasons: List[str] = field(default_factory=list)
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "decayed": self.decayed,
            "new_status": self.new_status,
            "reasons": list(self.reasons),
            "detail": dict(self.detail),
            "note": "decay records new state; evidence is preserved, never "
                    "deleted; decay is part of learning",
        }


@dataclass
class ConceptDecayEngine:
    """Records decay/rejection/merge/split as new state (never deletion)."""

    def evaluate(self, concept: ProtoConcept, *,
                 seen_this_tick: bool = True,
                 source_corrupted: bool = False) -> DecayResult:
        reasons: List[str] = []
        if not seen_this_tick and concept.recurrence_count <= 1:
            reasons.append(DecayReason.NOT_SEEN_AGAIN)
        # A concept only decays for failed prediction/compression when it is also
        # not earning its keep on the other utility axis (otherwise it survives).
        if (concept.prediction_utility <= 0.05 and concept.recurrence_count >= 3
                and concept.compression_utility < 0.3):
            reasons.append(DecayReason.PREDICTION_FAILED)
        if (concept.compression_utility <= 0.05 and concept.recurrence_count >= 3
                and concept.prediction_utility < 0.3):
            reasons.append(DecayReason.COMPRESSION_USELESS)
        if source_corrupted:
            reasons.append(DecayReason.SOURCE_CORRUPTED)
        if concept.human_label_contamination_score >= 0.75 \
                and concept.grounding_score < 0.2:
            reasons.append(DecayReason.LABEL_CONTAMINATION)
        if (concept.stability_score < 0.2
                and concept.recurrence_count == 1
                and concept.attention_utility < 0.2):
            reasons.append(DecayReason.FALSE_PATTERN)

        if not reasons:
            return DecayResult(concept_id=concept.concept_id, decayed=False,
                               new_status=concept.status)

        new_status = (ProtoConceptStatus.REJECTED
                      if DecayReason.FALSE_PATTERN in reasons
                      or DecayReason.LABEL_CONTAMINATION in reasons
                      else ProtoConceptStatus.DECAYING)
        concept.status = new_status
        if "decayed/rejected; retained as historical evidence" \
                not in concept.limitations:
            concept.limitations.append(
                "decayed/rejected; retained as historical evidence")
        return DecayResult(concept_id=concept.concept_id, decayed=True,
                           new_status=new_status, reasons=reasons)

    def merge(self, weaker: ProtoConcept,
              stronger: ProtoConcept) -> DecayResult:
        """Record a merge (weaker -> stronger); both remain visible."""
        weaker.status = ProtoConceptStatus.MERGED
        weaker.parent_concepts.append(stronger.concept_id)
        stronger.child_concepts.append(weaker.concept_id)
        return DecayResult(
            concept_id=weaker.concept_id, decayed=True,
            new_status=ProtoConceptStatus.MERGED,
            reasons=[DecayReason.MERGED],
            detail={"merged_into": stronger.concept_id})

    def split(self, parent: ProtoConcept,
              children: List[ProtoConcept]) -> DecayResult:
        """Record a split (parent -> children); parent remains visible."""
        parent.status = ProtoConceptStatus.SPLIT
        for c in children:
            parent.child_concepts.append(c.concept_id)
            c.parent_concepts.append(parent.concept_id)
        return DecayResult(
            concept_id=parent.concept_id, decayed=True,
            new_status=ProtoConceptStatus.SPLIT,
            reasons=[DecayReason.SPLIT],
            detail={"split_into": [c.concept_id for c in children]})
