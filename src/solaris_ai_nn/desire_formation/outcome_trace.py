"""Outcome trace -- the recorded result of a desire; failures/blocks are evidence.

A :class:`DesireOutcomeTrace` records what happened to a desire (satisfied, failed,
deferred, inhibited, decayed, safety/governance-blocked, no-action, internal action
completed/failed). Failed and blocked desires are evidence; no outcome is ever
deleted.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class OutcomeType:
    DESIRE_SATISFIED = "desire_satisfied"
    DESIRE_FAILED = "desire_failed"
    DESIRE_DEFERRED = "desire_deferred"
    DESIRE_INHIBITED = "desire_inhibited"
    DESIRE_DECAYED = "desire_decayed"
    DESIRE_SAFETY_BLOCKED = "desire_safety_blocked"
    DESIRE_GOVERNANCE_BLOCKED = "desire_governance_blocked"
    NO_ACTION_TAKEN = "no_action_taken"
    INTERNAL_ACTION_COMPLETED = "internal_action_completed"
    INTERNAL_ACTION_FAILED = "internal_action_failed"
    UNKNOWN = "unknown_outcome"

    ALL = (DESIRE_SATISFIED, DESIRE_FAILED, DESIRE_DEFERRED, DESIRE_INHIBITED,
           DESIRE_DECAYED, DESIRE_SAFETY_BLOCKED, DESIRE_GOVERNANCE_BLOCKED,
           NO_ACTION_TAKEN, INTERNAL_ACTION_COMPLETED, INTERNAL_ACTION_FAILED,
           UNKNOWN)


@dataclass
class DesireOutcome:
    """One recorded desire outcome (failures/blocks preserved as evidence)."""

    outcome_type: str
    desire_ref: str
    outcome_id: str = field(default_factory=lambda: f"OUT_{uuid.uuid4().hex[:8]}")
    selected_action_refs: List[str] = field(default_factory=list)
    outcome_evidence: List[str] = field(default_factory=list)
    later_sensory_consequence: str = ""
    prediction_update: str = ""
    memory_update: str = ""
    logos_tension_update: str = ""
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "outcome_type": self.outcome_type,
            "desire_ref": self.desire_ref,
            "selected_action_refs": list(self.selected_action_refs),
            "outcome_evidence": list(self.outcome_evidence),
            "later_sensory_consequence": self.later_sensory_consequence,
            "prediction_update": self.prediction_update,
            "memory_update": self.memory_update,
            "logos_tension_update": self.logos_tension_update,
            "limitations": list(self.limitations),
            "note": "failed/blocked/no-action outcomes are evidence; never "
                    "deleted",
        }


@dataclass
class DesireOutcomeTrace:
    """The set of outcome records this tick."""

    outcomes: List[DesireOutcome] = field(default_factory=list)

    def record(self, outcome_type: str, desire_ref: str, *,
               selected_action_refs: List[str] = None,
               outcome_evidence: List[str] = None) -> DesireOutcome:
        out = DesireOutcome(
            outcome_type=outcome_type, desire_ref=desire_ref,
            selected_action_refs=list(selected_action_refs or []),
            outcome_evidence=list(outcome_evidence or []))
        self.outcomes.append(out)
        return out

    def success_rate(self) -> float:
        decided = [o for o in self.outcomes
                   if o.outcome_type in (OutcomeType.DESIRE_SATISFIED,
                                         OutcomeType.INTERNAL_ACTION_COMPLETED,
                                         OutcomeType.DESIRE_FAILED,
                                         OutcomeType.INTERNAL_ACTION_FAILED)]
        if not decided:
            return 0.0
        ok = sum(1 for o in decided
                 if o.outcome_type in (OutcomeType.DESIRE_SATISFIED,
                                       OutcomeType.INTERNAL_ACTION_COMPLETED))
        return round(ok / len(decided), 4)

    def to_dict(self) -> Dict[str, Any]:
        dist: Dict[str, int] = {}
        for o in self.outcomes:
            dist[o.outcome_type] = dist.get(o.outcome_type, 0) + 1
        return {"outcome_count": len(self.outcomes),
                "success_rate": self.success_rate(),
                "distribution": dist,
                "outcomes": [o.to_dict() for o in self.outcomes]}
