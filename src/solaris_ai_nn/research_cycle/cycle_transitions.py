"""Research cycle transitions -- gate-checked, advisory stage moves.

:class:`CycleTransitionEngine` proposes the next stage transition from the
current stage, gated by the decision gates. Transitions require gate checks, a
blocked transition records its reason, no automatic external action occurs, and
no transition implies Solaris changed source code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .cycle_state import ResearchCycleStage


# Allowed forward transitions (and the recommendation branches from validated).
_ALLOWED = {
    ResearchCycleStage.BASELINE_SELECTED: [ResearchCycleStage.ROADMAP_DEFINED],
    ResearchCycleStage.ROADMAP_DEFINED: [
        ResearchCycleStage.ARCHITECTURE_EVIDENCE_LOADED],
    ResearchCycleStage.ARCHITECTURE_EVIDENCE_LOADED: [
        ResearchCycleStage.VARIANT_PROPOSED],
    ResearchCycleStage.VARIANT_PROPOSED: [
        ResearchCycleStage.EXPERIMENT_PACK_COMPILED],
    ResearchCycleStage.EXPERIMENT_PACK_COMPILED: [
        ResearchCycleStage.WAITING_FOR_EXTERNAL_IMPLEMENTATION],
    ResearchCycleStage.WAITING_FOR_EXTERNAL_IMPLEMENTATION: [
        ResearchCycleStage.IMPLEMENTATION_SUBMITTED],
    ResearchCycleStage.IMPLEMENTATION_SUBMITTED: [
        ResearchCycleStage.IMPLEMENTATION_AUDITED],
    ResearchCycleStage.IMPLEMENTATION_AUDITED: [
        ResearchCycleStage.WAITING_FOR_HUMAN_MERGE],
    ResearchCycleStage.WAITING_FOR_HUMAN_MERGE: [
        ResearchCycleStage.POST_MERGE_EVIDENCE_SUBMITTED],
    ResearchCycleStage.POST_MERGE_EVIDENCE_SUBMITTED: [
        ResearchCycleStage.POST_MERGE_ASSIMILATED],
    ResearchCycleStage.POST_MERGE_ASSIMILATED: [
        ResearchCycleStage.CANDIDATE_BASELINE_CREATED],
    ResearchCycleStage.CANDIDATE_BASELINE_CREATED: [
        ResearchCycleStage.RESEARCH_BASELINE_VALIDATED],
    ResearchCycleStage.RESEARCH_BASELINE_VALIDATED: [
        ResearchCycleStage.SOAK_RECOMMENDED,
        ResearchCycleStage.REPLICATION_RECOMMENDED,
        ResearchCycleStage.ARCHITECTURE_EVOLUTION_RECOMMENDED,
        ResearchCycleStage.CYCLE_COMPLETE],
    ResearchCycleStage.CYCLE_COMPLETE: [],
}


@dataclass
class TransitionCondition:
    """A condition that gates a transition (a gate must have passed)."""

    required_gate: str
    satisfied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"required_gate": self.required_gate,
                "satisfied": self.satisfied}


@dataclass
class ResearchCycleTransition:
    """A proposed (advisory) transition between stages."""

    from_stage: str
    to_stage: str
    allowed: bool
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"from_stage": self.from_stage, "to_stage": self.to_stage,
                "allowed": self.allowed, "reason": self.reason,
                "executes_external_action": False, "modifies_source": False}


@dataclass
class CycleTransitionEngine:
    """Proposes gate-checked stage transitions (advisory; executes nothing)."""

    def propose(self, current_stage: str, *, gates_passed: bool,
                blocked: bool) -> List[ResearchCycleTransition]:
        out: List[ResearchCycleTransition] = []
        # Any stage may transition to blocked when a blocker is present.
        if blocked:
            out.append(ResearchCycleTransition(
                from_stage=current_stage, to_stage=ResearchCycleStage.BLOCKED,
                allowed=True,
                reason="a blocker is present; transition to blocked is recorded"))
            return out
        for nxt in _ALLOWED.get(current_stage, []):
            if gates_passed:
                out.append(ResearchCycleTransition(
                    current_stage, nxt, allowed=True,
                    reason="gates passed; transition is permitted (advisory)"))
            else:
                out.append(ResearchCycleTransition(
                    current_stage, nxt, allowed=False,
                    reason="transition blocked: a decision gate has not passed"))
        if not out:
            out.append(ResearchCycleTransition(
                current_stage, current_stage, allowed=False,
                reason="terminal or unknown stage; no forward transition"))
        return out

    @staticmethod
    def is_allowed(from_stage: str, to_stage: str) -> bool:
        if to_stage == ResearchCycleStage.BLOCKED:
            return True
        if to_stage == ResearchCycleStage.ARCHIVED:
            return True
        return to_stage in _ALLOWED.get(from_stage, [])

    def to_dict(self, transitions: List[ResearchCycleTransition],
                ) -> Dict[str, Any]:
        return {
            "transition_count": len(transitions),
            "transitions": [t.to_dict() for t in transitions],
            "allowed_count": sum(1 for t in transitions if t.allowed),
            "note": "transitions are advisory and gate-checked; no automatic "
                    "external action occurs and no transition implies source "
                    "code changed by Solaris",
        }
