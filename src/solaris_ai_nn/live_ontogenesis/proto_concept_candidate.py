"""Live proto-concept candidate -- a feature-stability record, not a concept.

A :class:`LiveProtoConceptCandidate` groups recurring feature vectors that share a
feature signature. It preserves both supporting and contradicting evidence, tracks
recurrence and absence, records contamination findings and a stability score, and
carries a birth-gate result. A candidate is *not* a concept until it passes the
birth gate; weak, suspended, rejected, and contaminated candidates all remain
visible (false starts are never deleted).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ProtoConceptCandidateStatus:
    EMERGING = "emerging"
    STABILIZING = "stabilizing"
    STABLE_CANDIDATE = "stable_candidate"
    BORN = "born"
    WEAK = "weak"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    CONTAMINATED = "contaminated"
    SOURCE_ARTIFACT = "source_artifact"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"

    ALL = (EMERGING, STABILIZING, STABLE_CANDIDATE, BORN, WEAK, SUSPENDED,
           REJECTED, CONTAMINATED, SOURCE_ARTIFACT, INCONCLUSIVE, UNKNOWN)


@dataclass
class CandidateEvidence:
    """One piece of supporting evidence (an observed feature occurrence)."""

    event_id: str
    source_id: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "source_id": self.source_id,
                "detail": self.detail}


@dataclass
class CandidateCounterEvidence:
    """One piece of counterevidence challenging the candidate."""

    event_id: str
    source_id: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "source_id": self.source_id,
                "reason": self.reason}


@dataclass
class LiveProtoConceptCandidate:
    """A recurring feature signature that may (or may not) become a proto-concept."""

    candidate_id: str
    feature_signature: str
    source_distribution: Dict[str, int] = field(default_factory=dict)
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    recurrence_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    supporting_events: List[CandidateEvidence] = field(default_factory=list)
    contradicting_events: List[CandidateCounterEvidence] = field(
        default_factory=list)
    absence_windows: int = 0
    contamination_findings: List[str] = field(default_factory=list)
    stability_score: float = 0.0
    status: str = ProtoConceptCandidateStatus.EMERGING
    birth_gate_result: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)

    @property
    def supporting_count(self) -> int:
        return len(self.supporting_events)

    @property
    def counter_count(self) -> int:
        return len(self.contradicting_events)

    @property
    def source_count(self) -> int:
        return len(self.source_distribution)

    @property
    def operator_only(self) -> bool:
        srcs = set(self.source_distribution)
        return srcs == {"operator_pulse"} and bool(srcs)

    @property
    def is_concept(self) -> bool:
        return self.status == ProtoConceptCandidateStatus.BORN

    def add_support(self, event_id: str, source_id: str, detail: str = "") -> None:
        self.supporting_events.append(
            CandidateEvidence(event_id=event_id, source_id=source_id,
                              detail=detail))

    def add_counter(self, event_id: str, source_id: str, reason: str = "") -> None:
        self.contradicting_events.append(
            CandidateCounterEvidence(event_id=event_id, source_id=source_id,
                                     reason=reason))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "feature_signature": self.feature_signature,
            "source_distribution": dict(self.source_distribution),
            "modality_distribution": dict(self.modality_distribution),
            "recurrence_count": self.recurrence_count,
            "source_count": self.source_count,
            "first_seen": self.first_seen, "last_seen": self.last_seen,
            "supporting_count": self.supporting_count,
            "counter_count": self.counter_count,
            "supporting_events": [e.to_dict()
                                  for e in self.supporting_events[:50]],
            "contradicting_events": [e.to_dict()
                                     for e in self.contradicting_events[:50]],
            "absence_windows": self.absence_windows,
            "contamination_findings": list(self.contamination_findings),
            "stability_score": round(self.stability_score, 3),
            "status": self.status,
            "is_concept": self.is_concept,
            "birth_gate_result": dict(self.birth_gate_result),
            "limitations": list(self.limitations),
            "note": "a candidate is not a concept until it passes the birth "
                    "gate; supporting and contradicting evidence are preserved; "
                    "weak/rejected/contaminated candidates remain visible",
        }
