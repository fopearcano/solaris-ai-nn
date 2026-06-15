"""Desire candidates -- operational pressure toward an internal action tendency.

A :class:`DesireCandidate` is an operational pressure toward an *internal* action
(inspect, focus, stabilize, simulate, consolidate, preserve-unknown, no-action,
...). Desire is operational: it cannot command hardware/feeders, cannot modify
source files, cannot bypass governance or safety, and may lead only to internal
actions or safe simulated actions. It is NOT emotion and NOT human wanting.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .push import PushSource


class DesireKind:
    INSPECT_ABSENCE = "inspect_absence"
    FOCUS_MODALITY = "focus_modality"
    COMPARE_MODALITIES = "compare_modalities"
    STABILIZE_CONCEPT = "stabilize_concept"
    TEST_PREDICTION = "test_prediction"
    RUN_INTERNAL_SIMULATION = "run_internal_simulation"
    RESOLVE_LOGOS_TENSION = "resolve_LOGOS_tension"
    PRESERVE_UNKNOWN = "preserve_unknown"
    CONSOLIDATE_MEMORY = "consolidate_memory"
    REST_RECEPTOR = "rest_receptor"
    RECOVER_NEGLECTED_MODALITY = "recover_neglected_modality"
    MARK_SOURCE_UNRELIABLE = "mark_source_unreliable"
    REQUEST_OPERATOR_REVIEW = "request_operator_review"
    NO_ACTION = "no_action"
    UNKNOWN = "unknown"

    ALL = (INSPECT_ABSENCE, FOCUS_MODALITY, COMPARE_MODALITIES,
           STABILIZE_CONCEPT, TEST_PREDICTION, RUN_INTERNAL_SIMULATION,
           RESOLVE_LOGOS_TENSION, PRESERVE_UNKNOWN, CONSOLIDATE_MEMORY,
           REST_RECEPTOR, RECOVER_NEGLECTED_MODALITY, MARK_SOURCE_UNRELIABLE,
           REQUEST_OPERATOR_REVIEW, NO_ACTION, UNKNOWN)


class DesireStatus:
    CANDIDATE = "candidate"
    ACTIVE = "active"
    INHIBITED = "inhibited"
    DEFERRED = "deferred"
    SATISFIED = "satisfied"
    FAILED = "failed"
    DECAYED = "decayed"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    AMBIGUOUS = "ambiguous"

    ALL = (CANDIDATE, ACTIVE, INHIBITED, DEFERRED, SATISFIED, FAILED, DECAYED,
           BLOCKED_BY_SAFETY, AMBIGUOUS)


# Each push source proposes a desire kind (the internal tendency it implies).
_PUSH_TO_DESIRE = {
    PushSource.HIGH_NOVELTY: DesireKind.FOCUS_MODALITY,
    PushSource.UNRESOLVED_ABSENCE: DesireKind.INSPECT_ABSENCE,
    PushSource.FAILED_PREDICTION: DesireKind.TEST_PREDICTION,
    PushSource.STRONG_INVARIANT: DesireKind.STABILIZE_CONCEPT,
    PushSource.UNSTABLE_CONCEPT: DesireKind.STABILIZE_CONCEPT,
    PushSource.SIGN_AMBIGUITY: DesireKind.PRESERVE_UNKNOWN,
    PushSource.LOGOS_TENSION: DesireKind.RESOLVE_LOGOS_TENSION,
    PushSource.SOURCE_SILENCE: DesireKind.INSPECT_ABSENCE,
    PushSource.SOURCE_CORRUPTION: DesireKind.MARK_SOURCE_UNRELIABLE,
    PushSource.RECEPTOR_FATIGUE: DesireKind.REST_RECEPTOR,
    PushSource.OVERLOAD: DesireKind.NO_ACTION,
    PushSource.DEPRIVATION: DesireKind.RECOVER_NEGLECTED_MODALITY,
    PushSource.BOUNDARY_AMBIGUITY: DesireKind.REQUEST_OPERATOR_REVIEW,
    PushSource.CONTINUITY_BREAK: DesireKind.REQUEST_OPERATOR_REVIEW,
    PushSource.CONSOLIDATION_PRESSURE: DesireKind.CONSOLIDATE_MEMORY,
}

# The internal action each desire kind expects (allowed internal action kinds).
_DESIRE_TO_ACTION = {
    DesireKind.INSPECT_ABSENCE: "inspect_absence_window",
    DesireKind.FOCUS_MODALITY: "shift_attention",
    DesireKind.COMPARE_MODALITIES: "compare_modalities",
    DesireKind.STABILIZE_CONCEPT: "mark_concept_unstable",
    DesireKind.TEST_PREDICTION: "test_internal_prediction",
    DesireKind.RUN_INTERNAL_SIMULATION: "run_bounded_simulation",
    DesireKind.RESOLVE_LOGOS_TENSION: "generate_hypothesis",
    DesireKind.PRESERVE_UNKNOWN: "preserve_unknown",
    DesireKind.CONSOLIDATE_MEMORY: "trigger_consolidation_recommendation",
    DesireKind.REST_RECEPTOR: "decrease_internal_monitoring",
    DesireKind.RECOVER_NEGLECTED_MODALITY: "shift_attention",
    DesireKind.MARK_SOURCE_UNRELIABLE: "mark_source_unreliable",
    DesireKind.REQUEST_OPERATOR_REVIEW: "request_operator_review",
    DesireKind.NO_ACTION: "no_op",
    DesireKind.UNKNOWN: "no_op",
}


@dataclass
class DesireCandidate:
    """One operational desire candidate (internal action tendency, not wanting)."""

    kind: str
    desire_id: str = field(default_factory=lambda: f"DES_{uuid.uuid4().hex[:8]}")
    status: str = DesireStatus.CANDIDATE
    push_refs: List[str] = field(default_factory=list)
    valence_refs: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    expected_internal_action: str = ""
    expected_utility: float = 0.0
    expected_risk: float = 0.0
    urgency: float = 0.0
    confidence: float = 0.0
    uncertainty: float = 0.0
    safety_scope: str = "internal_only"
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.expected_internal_action:
            self.expected_internal_action = _DESIRE_TO_ACTION.get(
                self.kind, "no_op")
        if not self.limitations:
            self.limitations = [
                "operational pressure toward an internal action, not human "
                "wanting",
                "internal-only; cannot command hardware/feeders or modify "
                "source",
            ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "desire_id": self.desire_id,
            "kind": self.kind,
            "status": self.status,
            "push_refs": list(self.push_refs),
            "valence_refs": list(self.valence_refs),
            "source_refs": list(self.source_refs),
            "expected_internal_action": self.expected_internal_action,
            "expected_utility": round(self.expected_utility, 4),
            "expected_risk": round(self.expected_risk, 4),
            "urgency": round(self.urgency, 4),
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "safety_scope": self.safety_scope,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "note": "operational desire candidate; not emotion, not human "
                    "wanting, not conscious intention or free will",
        }


@dataclass
class DesireFormationEngine:
    """Forms desire candidates from pushes (operational, internal-only)."""

    desires: List[DesireCandidate] = field(default_factory=list)

    def form(self, pushes: List[Any], *,
             max_desires: int = 50) -> List[DesireCandidate]:
        self.desires = []
        for push in pushes:
            if len(self.desires) >= max_desires:
                break
            kind = _PUSH_TO_DESIRE.get(getattr(push, "source_type", ""),
                                       DesireKind.UNKNOWN)
            intensity = float(getattr(push, "intensity", 0.0))
            self.desires.append(DesireCandidate(
                kind=kind, push_refs=[getattr(push, "push_id", "")],
                valence_refs=list(getattr(push, "valence_refs", [])),
                source_refs=list(getattr(push, "source_refs", [])),
                expected_utility=intensity,
                expected_risk=round(0.2 if kind != DesireKind.NO_ACTION
                                    else 0.0, 4),
                urgency=float(getattr(push, "urgency", 0.0)),
                confidence=intensity,
                uncertainty=float(getattr(push, "uncertainty", 0.0)),
                evidence_refs=list(getattr(push, "evidence_refs", []))))
        return self.desires

    def to_dict(self) -> Dict[str, Any]:
        return {"desire_count": len(self.desires),
                "desires": [d.to_dict() for d in self.desires]}
