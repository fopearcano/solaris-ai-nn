"""Inhibition -- protecting the organism from unsafe or useless internal churn.

The :class:`InhibitionEngine` records when an internal action is inhibited and why.
Inhibition is NOT failure -- it protects the organism from useless or unsafe churn
-- and every inhibited action is recorded.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class InhibitionReason:
    SAFETY_RISK = "safety_risk"
    GOVERNANCE_REQUIRED = "governance_required"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    BOUNDARY_UNCERTAIN = "boundary_uncertain"
    SIMULATION_NOT_OBSERVATION = "simulation_not_observation"
    SOURCE_UNRELIABLE = "source_unreliable"
    OVERLOAD = "overload"
    ENERGY_BUDGET_LOW = "energy_budget_low"
    ATTENTION_CONFLICT = "attention_conflict"
    FALSE_PATTERN_RISK = "false_pattern_risk"
    HUMAN_LABEL_CONTAMINATION = "human_label_contamination"
    NO_EFFECT_HISTORY = "no_effect_history"
    UNKNOWN = "unknown"

    ALL = (SAFETY_RISK, GOVERNANCE_REQUIRED, INSUFFICIENT_EVIDENCE,
           BOUNDARY_UNCERTAIN, SIMULATION_NOT_OBSERVATION, SOURCE_UNRELIABLE,
           OVERLOAD, ENERGY_BUDGET_LOW, ATTENTION_CONFLICT, FALSE_PATTERN_RISK,
           HUMAN_LABEL_CONTAMINATION, NO_EFFECT_HISTORY, UNKNOWN)


@dataclass
class ActionInhibition:
    """One recorded inhibition of an internal action (not a failure)."""

    reason: str
    action_ref: str = ""
    inhibition_id: str = field(
        default_factory=lambda: f"INH_{uuid.uuid4().hex[:8]}")
    action_kind: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inhibition_id": self.inhibition_id,
            "reason": self.reason,
            "action_ref": self.action_ref,
            "action_kind": self.action_kind,
            "evidence_refs": list(self.evidence_refs),
            "note": "inhibition is not failure; it protects against unsafe/"
                    "useless internal churn and is always recorded",
        }


@dataclass
class InhibitionEngine:
    """Records action inhibitions with their reasons (preserved)."""

    inhibitions: List[ActionInhibition] = field(default_factory=list)

    def inhibit(self, reason: str, *, action_ref: str = "",
                action_kind: str = "",
                evidence_refs: List[str] = None) -> ActionInhibition:
        if reason not in InhibitionReason.ALL:
            reason = InhibitionReason.UNKNOWN
        inh = ActionInhibition(reason=reason, action_ref=action_ref,
                               action_kind=action_kind,
                               evidence_refs=list(evidence_refs or []))
        self.inhibitions.append(inh)
        return inh

    def distribution(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for i in self.inhibitions:
            out[i.reason] = out.get(i.reason, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {"inhibition_count": len(self.inhibitions),
                "distribution": self.distribution(),
                "inhibitions": [i.to_dict() for i in self.inhibitions]}
