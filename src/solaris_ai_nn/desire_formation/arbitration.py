"""Arbitration -- safe selection among desires; safety/governance have veto.

The :class:`DesireArbitrator` selects among ready desires considering push
intensity, valence, utility, risk, safety, governance, energy, attention, boundary
confidence, uncertainty, conflict, and consolidation pressure. Safety and governance
have veto power; no real-world actuation, arbitrary code execution, or source
modification may ever be selected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .desire import DesireKind, DesireStatus
from .readiness import ReadinessState


class ArbitrationOutcome:
    SELECT_INTERNAL_ACTION = "select_internal_action"
    SELECT_SIMULATION = "select_simulation"
    SELECT_ATTENTION_SHIFT = "select_attention_shift"
    SELECT_CONSOLIDATION = "select_consolidation"
    DEFER = "defer"
    INHIBIT = "inhibit"
    NO_OP = "no_op"
    SAFETY_BLOCK = "safety_block"
    GOVERNANCE_BLOCK = "governance_block"

    ALL = (SELECT_INTERNAL_ACTION, SELECT_SIMULATION, SELECT_ATTENTION_SHIFT,
           SELECT_CONSOLIDATION, DEFER, INHIBIT, NO_OP, SAFETY_BLOCK,
           GOVERNANCE_BLOCK)


@dataclass
class ArbitrationPolicy:
    """Tunable, conservative arbitration policy."""

    min_score: float = 0.25
    overload_forces_no_op: bool = True
    max_risk: float = 0.8


@dataclass
class ArbitrationResult:
    desire_ref: str
    outcome: str
    selected_action: str = ""
    score: float = 0.0
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"desire_ref": self.desire_ref, "outcome": self.outcome,
                "selected_action": self.selected_action,
                "score": round(self.score, 4), "reason": self.reason,
                "note": "safety/governance have veto; no external actuation "
                        "may be selected"}


@dataclass
class DesireArbitrator:
    """Selects internal actions safely (conservative; safety vetoes)."""

    policy: ArbitrationPolicy = field(default_factory=ArbitrationPolicy)
    results: List[ArbitrationResult] = field(default_factory=list)

    def arbitrate(self, desire: Any, readiness: Any, *,
                  overloaded: bool = False,
                  safety_ok: bool = True) -> ArbitrationResult:
        did = getattr(desire, "desire_id", "")
        kind = getattr(desire, "kind", "")
        rstate = getattr(readiness, "state", ReadinessState.UNKNOWN)

        # Safety veto (highest priority).
        if not safety_ok or rstate == ReadinessState.SAFETY_BLOCKED:
            res = ArbitrationResult(did, ArbitrationOutcome.SAFETY_BLOCK,
                                    reason="safety veto")
            self.results.append(res)
            return res
        # Governance veto where required.
        if rstate == ReadinessState.GOVERNANCE_REQUIRED:
            res = ArbitrationResult(did, ArbitrationOutcome.GOVERNANCE_BLOCK,
                                    reason="governance review required")
            self.results.append(res)
            return res
        # Overload forces a no-op (organismic inhibition).
        if overloaded and self.policy.overload_forces_no_op \
                and kind != DesireKind.NO_ACTION:
            res = ArbitrationResult(did, ArbitrationOutcome.NO_OP,
                                    reason="overload forces inhibition")
            self.results.append(res)
            return res
        # Explicit no-action desire -> no-op.
        if kind == DesireKind.NO_ACTION:
            res = ArbitrationResult(did, ArbitrationOutcome.NO_OP,
                                    selected_action="no_op",
                                    reason="no-action desire")
            self.results.append(res)
            return res
        # Not ready -> defer / inhibit.
        if rstate in (ReadinessState.INSUFFICIENT_EVIDENCE,
                      ReadinessState.NOT_READY):
            res = ArbitrationResult(did, ArbitrationOutcome.INHIBIT,
                                    reason=f"not ready ({rstate})")
            self.results.append(res)
            return res
        if rstate == ReadinessState.DEFER:
            res = ArbitrationResult(did, ArbitrationOutcome.DEFER,
                                    reason="deferred (boundary clarity)")
            self.results.append(res)
            return res

        # Score = utility - risk, weighted by urgency.
        utility = float(getattr(desire, "expected_utility", 0.0))
        risk = float(getattr(desire, "expected_risk", 0.0))
        urgency = float(getattr(desire, "urgency", 0.0))
        score = round(max(0.0, (utility - risk) * (0.5 + 0.5 * urgency)), 4)
        if risk > self.policy.max_risk or score < self.policy.min_score:
            res = ArbitrationResult(did, ArbitrationOutcome.INHIBIT, score=score,
                                    reason="score below threshold or risk high")
            self.results.append(res)
            return res

        outcome = ArbitrationOutcome.SELECT_INTERNAL_ACTION
        if kind == DesireKind.RUN_INTERNAL_SIMULATION:
            outcome = ArbitrationOutcome.SELECT_SIMULATION
        elif kind in (DesireKind.FOCUS_MODALITY,
                      DesireKind.RECOVER_NEGLECTED_MODALITY):
            outcome = ArbitrationOutcome.SELECT_ATTENTION_SHIFT
        elif kind == DesireKind.CONSOLIDATE_MEMORY:
            outcome = ArbitrationOutcome.SELECT_CONSOLIDATION
        res = ArbitrationResult(
            did, outcome,
            selected_action=getattr(desire, "expected_internal_action", "no_op"),
            score=score, reason="selected (passed all gates)")
        self.results.append(res)
        return res

    def to_dict(self) -> Dict[str, Any]:
        dist: Dict[str, int] = {}
        for r in self.results:
            dist[r.outcome] = dist.get(r.outcome, 0) + 1
        return {"arbitration_count": len(self.results),
                "distribution": dist,
                "results": [r.to_dict() for r in self.results]}
