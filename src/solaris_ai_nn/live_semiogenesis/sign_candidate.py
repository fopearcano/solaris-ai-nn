"""Live sign candidate -- a private internal reference, not yet a born sign.

A :class:`LiveSignCandidate` links a private internal token to one or more live
proto-concepts. It preserves supporting and contradicting evidence, records utility
evidence and contamination findings, and carries a birth-gate result. A candidate is
*not* a born sign until it passes the sign birth gate; weak, suspended, rejected,
and contaminated candidates all remain visible. Sign tokens are internal/private and
are never copied from human labels by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SignCandidateStatus:
    EMERGING = "emerging"
    STABILIZING = "stabilizing"
    STABLE_CANDIDATE = "stable_candidate"
    BORN = "born"
    WEAK = "weak"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    CONTAMINATED = "contaminated"
    LABEL_DEPENDENT = "label_dependent"
    GLOSS_DEPENDENT = "gloss_dependent"
    OPERATOR_DEPENDENT = "operator_dependent"
    SOURCE_ARTIFACT = "source_artifact"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"

    ALL = (EMERGING, STABILIZING, STABLE_CANDIDATE, BORN, WEAK, SUSPENDED,
           REJECTED, CONTAMINATED, LABEL_DEPENDENT, GLOSS_DEPENDENT,
           OPERATOR_DEPENDENT, SOURCE_ARTIFACT, INCONCLUSIVE, UNKNOWN)


@dataclass
class SignEvidence:
    """One piece of supporting evidence for a sign (a concept/event reference)."""

    ref: str
    kind: str = "concept"
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"ref": self.ref, "kind": self.kind, "detail": self.detail}


@dataclass
class SignCounterEvidence:
    """One piece of counterevidence challenging a sign."""

    ref: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"ref": self.ref, "reason": self.reason}


@dataclass
class LiveSignCandidate:
    """A private sign candidate over one or more live proto-concepts."""

    sign_id: str
    private_token: str
    linked_concept_ids: List[str] = field(default_factory=list)
    feature_signature_refs: List[str] = field(default_factory=list)
    source_distribution: Dict[str, int] = field(default_factory=dict)
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    supporting_events: List[SignEvidence] = field(default_factory=list)
    contradicting_events: List[SignCounterEvidence] = field(default_factory=list)
    utility_evidence: Dict[str, Any] = field(default_factory=dict)
    utility_score: float = 0.0
    contamination_findings: List[str] = field(default_factory=list)
    status: str = SignCandidateStatus.EMERGING
    birth_gate_result: Dict[str, Any] = field(default_factory=dict)
    debug_alias: str = ""  # NON-ground-truth human-readable annotation only
    limitations: List[str] = field(default_factory=list)

    @property
    def supporting_count(self) -> int:
        return len(self.supporting_events)

    @property
    def counter_count(self) -> int:
        return len(self.contradicting_events)

    @property
    def is_sign(self) -> bool:
        return self.status == SignCandidateStatus.BORN

    def add_support(self, ref: str, kind: str = "concept", detail: str = "") -> None:
        self.supporting_events.append(SignEvidence(ref=ref, kind=kind,
                                                   detail=detail))

    def add_counter(self, ref: str, reason: str = "") -> None:
        self.contradicting_events.append(
            SignCounterEvidence(ref=ref, reason=reason))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id, "private_token": self.private_token,
            "linked_concept_ids": list(self.linked_concept_ids),
            "feature_signature_refs": list(self.feature_signature_refs),
            "source_distribution": dict(self.source_distribution),
            "modality_distribution": dict(self.modality_distribution),
            "supporting_count": self.supporting_count,
            "counter_count": self.counter_count,
            "supporting_events": [e.to_dict()
                                  for e in self.supporting_events[:50]],
            "contradicting_events": [e.to_dict()
                                     for e in self.contradicting_events[:50]],
            "utility_evidence": dict(self.utility_evidence),
            "utility_score": round(self.utility_score, 3),
            "contamination_findings": list(self.contamination_findings),
            "status": self.status, "is_sign": self.is_sign,
            "birth_gate_result": dict(self.birth_gate_result),
            "debug_alias": self.debug_alias,
            "debug_alias_is_ground_truth": False,
            "limitations": list(self.limitations),
            "note": "a sign candidate is not a born sign until it passes the "
                    "sign birth gate; the token is private/internal; supporting "
                    "and contradicting evidence are preserved; weak/rejected/"
                    "contaminated candidates remain visible",
        }
