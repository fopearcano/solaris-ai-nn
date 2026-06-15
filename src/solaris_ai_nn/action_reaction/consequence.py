"""Consequence trace -- evidence-backed before/after change of an action.

A :class:`ConsequenceTrace` links an action and its reaction to an observed
before/after internal change over a bounded time window. Consequences are
evidence-backed; effects are never invented; if the effect cannot be determined the
trace records ambiguous / no-observed-change.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ConsequenceType:
    IMMEDIATE_INTERNAL_CHANGE = "immediate_internal_change"
    DELAYED_INTERNAL_CHANGE = "delayed_internal_change"
    PREDICTION_OUTCOME = "prediction_outcome"
    ATTENTION_CHANGE = "attention_change"
    METABOLIC_CHANGE = "metabolic_change"
    CONCEPT_CHANGE = "concept_change"
    SIGN_CHANGE = "sign_change"
    BOUNDARY_CHANGE = "boundary_change"
    MEMORY_CHANGE = "memory_change"
    LOGOS_CHANGE = "LOGOS_change"
    HYPOTHESIS_CHANGE = "hypothesis_change"
    NO_OBSERVED_CHANGE = "no_observed_change"
    UNSAFE_BLOCK = "unsafe_block"
    AMBIGUOUS_EFFECT = "ambiguous_effect"

    ALL = (IMMEDIATE_INTERNAL_CHANGE, DELAYED_INTERNAL_CHANGE,
           PREDICTION_OUTCOME, ATTENTION_CHANGE, METABOLIC_CHANGE,
           CONCEPT_CHANGE, SIGN_CHANGE, BOUNDARY_CHANGE, MEMORY_CHANGE,
           LOGOS_CHANGE, HYPOTHESIS_CHANGE, NO_OBSERVED_CHANGE, UNSAFE_BLOCK,
           AMBIGUOUS_EFFECT)


@dataclass
class ConsequenceWindow:
    start_tick: int = 0
    end_tick: int = 0

    @property
    def length(self) -> int:
        return max(0, self.end_tick - self.start_tick)

    def to_dict(self) -> Dict[str, Any]:
        return {"start_tick": self.start_tick, "end_tick": self.end_tick,
                "length": self.length}


@dataclass
class ConsequenceTrace:
    """One evidence-backed action consequence (or ambiguous/no-change)."""

    consequence_type: str
    action_refs: List[str] = field(default_factory=list)
    reaction_refs: List[str] = field(default_factory=list)
    consequence_id: str = field(
        default_factory=lambda: f"CSQ_{uuid.uuid4().hex[:8]}")
    before_state_summary: Dict[str, Any] = field(default_factory=dict)
    after_state_summary: Dict[str, Any] = field(default_factory=dict)
    window: ConsequenceWindow = field(default_factory=ConsequenceWindow)
    evidence_refs: List[str] = field(default_factory=list)
    uncertainty: float = 0.0
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.limitations:
            self.limitations = [
                "evidence-backed; effects are not invented",
                "ambiguous / no-observed-change is recorded when undetermined",
            ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consequence_id": self.consequence_id,
            "consequence_type": self.consequence_type,
            "action_refs": list(self.action_refs),
            "reaction_refs": list(self.reaction_refs),
            "before_state_summary": dict(self.before_state_summary),
            "after_state_summary": dict(self.after_state_summary),
            "window": self.window.to_dict(),
            "evidence_refs": list(self.evidence_refs),
            "uncertainty": round(self.uncertainty, 4),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "note": "consequence is evidence-backed; not invented",
        }


# Maps a reaction kind onto the consequence type it implies.
_REACTION_TO_CONSEQUENCE = {
    "uncertainty_reduced": ConsequenceType.IMMEDIATE_INTERNAL_CHANGE,
    "uncertainty_increased": ConsequenceType.IMMEDIATE_INTERNAL_CHANGE,
    "prediction_confirmed": ConsequenceType.PREDICTION_OUTCOME,
    "prediction_failed": ConsequenceType.PREDICTION_OUTCOME,
    "absence_confirmed": ConsequenceType.PREDICTION_OUTCOME,
    "overload_reduced": ConsequenceType.METABOLIC_CHANGE,
    "overload_increased": ConsequenceType.METABOLIC_CHANGE,
    "deprivation_integrated": ConsequenceType.METABOLIC_CHANGE,
    "concept_stabilized": ConsequenceType.CONCEPT_CHANGE,
    "concept_destabilized": ConsequenceType.CONCEPT_CHANGE,
    "sign_stabilized": ConsequenceType.SIGN_CHANGE,
    "sign_drift_detected": ConsequenceType.SIGN_CHANGE,
    "boundary_clarified": ConsequenceType.BOUNDARY_CHANGE,
    "boundary_confused": ConsequenceType.BOUNDARY_CHANGE,
    "LOGOS_tension_reduced": ConsequenceType.LOGOS_CHANGE,
    "LOGOS_tension_increased": ConsequenceType.LOGOS_CHANGE,
    "false_pattern_detected": ConsequenceType.CONCEPT_CHANGE,
    "no_effect": ConsequenceType.NO_OBSERVED_CHANGE,
    "blocked_by_safety": ConsequenceType.UNSAFE_BLOCK,
    "blocked_by_governance": ConsequenceType.UNSAFE_BLOCK,
    "unknown": ConsequenceType.AMBIGUOUS_EFFECT,
}


def consequence_type_for_reaction(reaction_kind: str) -> str:
    return _REACTION_TO_CONSEQUENCE.get(reaction_kind,
                                        ConsequenceType.AMBIGUOUS_EFFECT)
