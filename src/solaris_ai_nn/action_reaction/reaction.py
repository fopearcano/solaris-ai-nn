"""Reaction model -- the operational effect of an internal action, not feeling.

A :class:`SensoriumReaction` is the operational consequence of an internal action
(uncertainty reduced/increased, prediction confirmed/failed, overload reduced, ...).
Reaction valence is operational effect (constructive/disruptive/stabilizing/...),
NOT feeling and NOT pleasure/pain. A failed or blocked action still produces a
reaction trace.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .action_model import ActionKind


class ReactionKind:
    UNCERTAINTY_REDUCED = "uncertainty_reduced"
    UNCERTAINTY_INCREASED = "uncertainty_increased"
    PREDICTION_CONFIRMED = "prediction_confirmed"
    PREDICTION_FAILED = "prediction_failed"
    ABSENCE_CONFIRMED = "absence_confirmed"
    FALSE_PATTERN_DETECTED = "false_pattern_detected"
    CONCEPT_STABILIZED = "concept_stabilized"
    CONCEPT_DESTABILIZED = "concept_destabilized"
    SIGN_STABILIZED = "sign_stabilized"
    SIGN_DRIFT_DETECTED = "sign_drift_detected"
    OVERLOAD_REDUCED = "overload_reduced"
    OVERLOAD_INCREASED = "overload_increased"
    DEPRIVATION_INTEGRATED = "deprivation_integrated"
    BOUNDARY_CLARIFIED = "boundary_clarified"
    BOUNDARY_CONFUSED = "boundary_confused"
    LOGOS_TENSION_REDUCED = "LOGOS_tension_reduced"
    LOGOS_TENSION_INCREASED = "LOGOS_tension_increased"
    NO_EFFECT = "no_effect"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_GOVERNANCE = "blocked_by_governance"
    UNKNOWN = "unknown"

    ALL = (UNCERTAINTY_REDUCED, UNCERTAINTY_INCREASED, PREDICTION_CONFIRMED,
           PREDICTION_FAILED, ABSENCE_CONFIRMED, FALSE_PATTERN_DETECTED,
           CONCEPT_STABILIZED, CONCEPT_DESTABILIZED, SIGN_STABILIZED,
           SIGN_DRIFT_DETECTED, OVERLOAD_REDUCED, OVERLOAD_INCREASED,
           DEPRIVATION_INTEGRATED, BOUNDARY_CLARIFIED, BOUNDARY_CONFUSED,
           LOGOS_TENSION_REDUCED, LOGOS_TENSION_INCREASED, NO_EFFECT,
           BLOCKED_BY_SAFETY, BLOCKED_BY_GOVERNANCE, UNKNOWN)


class ReactionValence:
    CONSTRUCTIVE = "constructive"
    DISRUPTIVE = "disruptive"
    STABILIZING = "stabilizing"
    DESTABILIZING = "destabilizing"
    NEUTRAL = "neutral"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"

    ALL = (CONSTRUCTIVE, DISRUPTIVE, STABILIZING, DESTABILIZING, NEUTRAL,
           AMBIGUOUS, UNKNOWN)


_REACTION_VALENCE = {
    ReactionKind.UNCERTAINTY_REDUCED: ReactionValence.CONSTRUCTIVE,
    ReactionKind.UNCERTAINTY_INCREASED: ReactionValence.DISRUPTIVE,
    ReactionKind.PREDICTION_CONFIRMED: ReactionValence.CONSTRUCTIVE,
    ReactionKind.PREDICTION_FAILED: ReactionValence.DISRUPTIVE,
    ReactionKind.ABSENCE_CONFIRMED: ReactionValence.CONSTRUCTIVE,
    ReactionKind.FALSE_PATTERN_DETECTED: ReactionValence.CONSTRUCTIVE,
    ReactionKind.CONCEPT_STABILIZED: ReactionValence.STABILIZING,
    ReactionKind.CONCEPT_DESTABILIZED: ReactionValence.DESTABILIZING,
    ReactionKind.SIGN_STABILIZED: ReactionValence.STABILIZING,
    ReactionKind.SIGN_DRIFT_DETECTED: ReactionValence.DESTABILIZING,
    ReactionKind.OVERLOAD_REDUCED: ReactionValence.STABILIZING,
    ReactionKind.OVERLOAD_INCREASED: ReactionValence.DESTABILIZING,
    ReactionKind.DEPRIVATION_INTEGRATED: ReactionValence.CONSTRUCTIVE,
    ReactionKind.BOUNDARY_CLARIFIED: ReactionValence.CONSTRUCTIVE,
    ReactionKind.BOUNDARY_CONFUSED: ReactionValence.DISRUPTIVE,
    ReactionKind.LOGOS_TENSION_REDUCED: ReactionValence.STABILIZING,
    ReactionKind.LOGOS_TENSION_INCREASED: ReactionValence.DESTABILIZING,
    ReactionKind.NO_EFFECT: ReactionValence.NEUTRAL,
    ReactionKind.BLOCKED_BY_SAFETY: ReactionValence.NEUTRAL,
    ReactionKind.BLOCKED_BY_GOVERNANCE: ReactionValence.NEUTRAL,
    ReactionKind.UNKNOWN: ReactionValence.UNKNOWN,
}

# Expected reaction for each action kind (provisional, used by effect learning).
_EXPECTED_REACTION = {
    ActionKind.SHIFT_ATTENTION: ReactionKind.UNCERTAINTY_REDUCED,
    ActionKind.INSPECT_ABSENCE_WINDOW: ReactionKind.ABSENCE_CONFIRMED,
    ActionKind.RUN_BOUNDED_SIMULATION: ReactionKind.PREDICTION_CONFIRMED,
    ActionKind.TEST_INTERNAL_PREDICTION: ReactionKind.PREDICTION_CONFIRMED,
    ActionKind.PRESERVE_UNKNOWN: ReactionKind.FALSE_PATTERN_DETECTED,
    ActionKind.MARK_SOURCE_UNRELIABLE: ReactionKind.PREDICTION_CONFIRMED,
    ActionKind.MARK_CONCEPT_UNSTABLE: ReactionKind.CONCEPT_DESTABILIZED,
    ActionKind.MARK_SIGN_AMBIGUOUS: ReactionKind.SIGN_DRIFT_DETECTED,
    ActionKind.TRIGGER_CONSOLIDATION: ReactionKind.SIGN_STABILIZED,
    ActionKind.COMPARE_MODALITIES: ReactionKind.BOUNDARY_CLARIFIED,
    ActionKind.GENERATE_HYPOTHESIS: ReactionKind.LOGOS_TENSION_REDUCED,
    ActionKind.DECREASE_MONITORING: ReactionKind.OVERLOAD_REDUCED,
    ActionKind.NO_OP: ReactionKind.OVERLOAD_REDUCED,
}


@dataclass
class SensoriumReaction:
    """One operational reaction to an action (effect, not feeling)."""

    kind: str
    action_ref: str = ""
    reaction_id: str = field(default_factory=lambda: f"RXN_{uuid.uuid4().hex[:8]}")
    valence: str = ""
    magnitude: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.valence:
            self.valence = _REACTION_VALENCE.get(self.kind,
                                                 ReactionValence.UNKNOWN)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reaction_id": self.reaction_id,
            "kind": self.kind,
            "action_ref": self.action_ref,
            "valence": self.valence,
            "magnitude": round(self.magnitude, 4),
            "evidence_refs": list(self.evidence_refs),
            "note": "operational effect, not feeling and not pleasure/pain",
        }


@dataclass
class ReactionAssessment:
    """Assesses the reaction of an action from before/after state deltas."""

    @staticmethod
    def expected_reaction(action_kind: str) -> str:
        return _EXPECTED_REACTION.get(action_kind, ReactionKind.UNKNOWN)

    def assess(self, action: Any, *, before: Dict[str, Any],
               after: Dict[str, Any]) -> SensoriumReaction:
        kind = getattr(action, "kind", "")
        status = getattr(action, "status", "executed")
        action_ref = getattr(action, "action_id", "")
        if status == "blocked":
            return SensoriumReaction(
                kind=ReactionKind.BLOCKED_BY_SAFETY, action_ref=action_ref,
                evidence_refs=["blocked"])
        # Compare an "uncertainty"-like before/after metric where available.
        before_u = float(before.get("uncertainty", 0.0) or 0.0)
        after_u = float(after.get("uncertainty", before_u) or before_u)
        if kind == ActionKind.NO_OP:
            return SensoriumReaction(kind=ReactionKind.OVERLOAD_REDUCED,
                                     action_ref=action_ref, magnitude=0.2,
                                     evidence_refs=["no_op"])
        expected = self.expected_reaction(kind)
        if expected == ReactionKind.UNKNOWN:
            return SensoriumReaction(kind=ReactionKind.NO_EFFECT,
                                     action_ref=action_ref,
                                     evidence_refs=["no_expected_reaction"])
        # If an uncertainty delta is present, use it; else credit expected effect.
        if after_u < before_u:
            return SensoriumReaction(kind=ReactionKind.UNCERTAINTY_REDUCED,
                                     action_ref=action_ref,
                                     magnitude=round(before_u - after_u, 4),
                                     evidence_refs=["uncertainty_delta"])
        return SensoriumReaction(kind=expected, action_ref=action_ref,
                                 magnitude=0.3, evidence_refs=["expected_effect"])
