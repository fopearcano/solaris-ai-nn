"""Live cognition trace -- an operational anticipation/relation record.

A :class:`LiveCognitionTrace` links private signs and proto-concepts to an
anticipation, a relation traversal, or an internal simulation, and preserves both
supporting and contradicting evidence plus an uncertainty state and a prediction
assessment. A trace is **not** proof of reasoning; it is an operational record.
Weak, suspended, rejected, and contaminated traces all remain visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class CognitionTraceStatus:
    EMERGING = "emerging"
    ACTIVE = "active"
    STABLE = "stable"
    USEFUL = "useful"
    WEAK = "weak"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    CONTAMINATED = "contaminated"
    SPURIOUS_RELATION = "spurious_relation"
    SOURCE_ARTIFACT = "source_artifact"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"

    ALL = (EMERGING, ACTIVE, STABLE, USEFUL, WEAK, SUSPENDED, REJECTED,
           CONTAMINATED, SPURIOUS_RELATION, SOURCE_ARTIFACT, INCONCLUSIVE,
           UNKNOWN)


@dataclass
class CognitionEvidence:
    """One piece of supporting evidence for a trace."""

    ref: str
    kind: str = "sign"
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"ref": self.ref, "kind": self.kind, "detail": self.detail}


@dataclass
class CognitionCounterEvidence:
    """One piece of counterevidence challenging a trace."""

    ref: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"ref": self.ref, "reason": self.reason}


@dataclass
class LiveCognitionTrace:
    """An operational sign-based anticipation / relation record."""

    trace_id: str
    linked_sign_ids: List[str] = field(default_factory=list)
    linked_concept_ids: List[str] = field(default_factory=list)
    relation_refs: List[str] = field(default_factory=list)
    input_event_refs: List[str] = field(default_factory=list)
    anticipated_event_refs: List[str] = field(default_factory=list)
    observed_outcome_refs: List[str] = field(default_factory=list)
    uncertainty_state: Dict[str, Any] = field(default_factory=dict)
    prediction_assessment: Dict[str, Any] = field(default_factory=dict)
    contamination_findings: List[str] = field(default_factory=list)
    supporting_evidence: List[CognitionEvidence] = field(default_factory=list)
    contradicting_evidence: List[CognitionCounterEvidence] = field(
        default_factory=list)
    kind: str = "relation"  # relation / anticipation / simulation
    status: str = CognitionTraceStatus.EMERGING
    limitations: List[str] = field(default_factory=list)

    @property
    def supporting_count(self) -> int:
        return len(self.supporting_evidence)

    @property
    def counter_count(self) -> int:
        return len(self.contradicting_evidence)

    @property
    def uncertainty(self) -> float:
        return float(self.uncertainty_state.get("uncertainty", 1.0))

    @property
    def promoted(self) -> bool:
        return self.status in (CognitionTraceStatus.STABLE,
                               CognitionTraceStatus.USEFUL)

    def add_support(self, ref: str, kind: str = "sign", detail: str = "") -> None:
        self.supporting_evidence.append(
            CognitionEvidence(ref=ref, kind=kind, detail=detail))

    def add_counter(self, ref: str, reason: str = "") -> None:
        self.contradicting_evidence.append(
            CognitionCounterEvidence(ref=ref, reason=reason))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id, "kind": self.kind,
            "linked_sign_ids": list(self.linked_sign_ids),
            "linked_concept_ids": list(self.linked_concept_ids),
            "relation_refs": list(self.relation_refs),
            "input_event_refs": self.input_event_refs[:50],
            "anticipated_event_refs": self.anticipated_event_refs[:50],
            "observed_outcome_refs": self.observed_outcome_refs[:50],
            "uncertainty_state": dict(self.uncertainty_state),
            "uncertainty": round(self.uncertainty, 3),
            "prediction_assessment": dict(self.prediction_assessment),
            "contamination_findings": list(self.contamination_findings),
            "supporting_count": self.supporting_count,
            "counter_count": self.counter_count,
            "supporting_evidence": [e.to_dict()
                                    for e in self.supporting_evidence[:50]],
            "contradicting_evidence": [e.to_dict()
                                       for e in self.contradicting_evidence[:50]],
            "status": self.status, "promoted": self.promoted,
            "limitations": list(self.limitations),
            "note": "a cognition trace is an operational relation/anticipation "
                    "record, not proof of reasoning; supporting and "
                    "contradicting evidence are preserved; weak/rejected/"
                    "contaminated traces remain visible",
        }
