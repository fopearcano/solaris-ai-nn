"""Evidence mapping -- many-to-many links between claims and evidence.

:class:`EvidenceMap` links claims to evidence drawn from every research layer
(research baseline, research cycle, architecture evolution, developmental soak,
replication/falsification, developmental life, sensorium differentiation,
perceptual metabolism, ontogenesis, semiogenesis, cognition, self-boundary,
desire formation, action-reaction, implementation intake, post-merge assimilation,
safety invariants, evaluation, operator notes). Mapping is many-to-many,
contradictory evidence is preserved, missing evidence is explicit, and no claim
can be "supported" without evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


EVIDENCE_SOURCES = (
    "research_baseline", "research_cycle", "architecture_evolution",
    "developmental_soak", "replication_falsification", "developmental_life",
    "sensorium_differentiation", "perceptual_metabolism", "ontogenesis",
    "semiogenesis", "cognition", "self_boundary", "desire_formation",
    "action_reaction", "implementation_intake", "post_merge_assimilation",
    "safety_invariants", "evaluation", "operator_notes",
)


class EvidenceRole:
    SUPPORTS = "supports"
    WEAKLY_SUPPORTS = "weakly_supports"
    CONTRADICTS = "contradicts"
    FALSIFIES = "falsifies"
    LIMITS = "limits"
    CONTEXTUALIZES = "contextualizes"
    MISSING = "missing"
    INCONCLUSIVE = "inconclusive"
    NEGATIVE_RESULT = "negative_result"
    SAFETY_BOUNDARY = "safety_boundary"

    ALL = (SUPPORTS, WEAKLY_SUPPORTS, CONTRADICTS, FALSIFIES, LIMITS,
           CONTEXTUALIZES, MISSING, INCONCLUSIVE, NEGATIVE_RESULT,
           SAFETY_BOUNDARY)

    SUPPORTING = (SUPPORTS, WEAKLY_SUPPORTS)
    AGAINST = (CONTRADICTS, FALSIFIES)


@dataclass
class MappedEvidence:
    """One piece of evidence mapped to a claim, with its role and source."""

    evidence_id: str
    source: str
    role: str = EvidenceRole.CONTEXTUALIZES
    detail: str = ""

    def __post_init__(self) -> None:
        if self.role not in EvidenceRole.ALL:
            self.role = EvidenceRole.INCONCLUSIVE
        if self.source not in EVIDENCE_SOURCES:
            self.source = "operator_notes"

    def to_dict(self) -> Dict[str, Any]:
        return {"evidence_id": self.evidence_id, "source": self.source,
                "role": self.role, "detail": self.detail}


@dataclass
class EvidenceMap:
    """Many-to-many map of claim_id -> mapped evidence (contradictions kept)."""

    mapping: Dict[str, List[MappedEvidence]] = field(default_factory=dict)

    def map_evidence(self, claim_id: str, evidence: MappedEvidence) -> None:
        self.mapping.setdefault(claim_id, []).append(evidence)

    def for_claim(self, claim_id: str) -> List[MappedEvidence]:
        return list(self.mapping.get(claim_id, []))

    def supporting_refs(self, claim_id: str) -> List[str]:
        return [e.evidence_id for e in self.mapping.get(claim_id, [])
                if e.role in EvidenceRole.SUPPORTING]

    def against_refs(self, claim_id: str) -> List[str]:
        return [e.evidence_id for e in self.mapping.get(claim_id, [])
                if e.role in EvidenceRole.AGAINST]

    def missing_refs(self, claim_id: str) -> List[str]:
        return [e.evidence_id for e in self.mapping.get(claim_id, [])
                if e.role == EvidenceRole.MISSING]

    def has_support(self, claim_id: str) -> bool:
        return bool(self.supporting_refs(claim_id))

    def has_contradiction(self, claim_id: str) -> bool:
        return bool(self.against_refs(claim_id))

    @property
    def evidence_mapping_count(self) -> int:
        return sum(len(v) for v in self.mapping.values())

    @property
    def contradiction_count(self) -> int:
        return sum(1 for v in self.mapping.values() for e in v
                   if e.role in EvidenceRole.AGAINST)

    @property
    def missing_count(self) -> int:
        return sum(1 for v in self.mapping.values() for e in v
                   if e.role == EvidenceRole.MISSING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_mapping_count": self.evidence_mapping_count,
            "claim_count": len(self.mapping),
            "contradiction_count": self.contradiction_count,
            "missing_count": self.missing_count,
            "mapping": {cid: [e.to_dict() for e in evs]
                        for cid, evs in self.mapping.items()},
            "note": "evidence mapping is many-to-many; contradictory evidence is "
                    "preserved, missing evidence is explicit, and no claim can be "
                    "supported without evidence",
        }
