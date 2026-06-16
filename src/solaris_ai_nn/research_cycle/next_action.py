"""Research cycle next action -- instructions for the operator, never executed.

:class:`NextActionPlanner` recommends the next operator action from the current
cycle stage and blockers. Next actions are instructions for the human/operator;
none is executed automatically; high-risk actions carry safety context; and if
the cycle is blocked, the next action is blocker resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .cycle_state import ResearchCycleStage


class NextActionType:
    REVIEW_CURRENT_BASELINE = "review_current_baseline"
    RUN_ARCHITECTURE_EVOLUTION = "run_architecture_evolution"
    COMPILE_EXPERIMENT_PACK = "compile_experiment_pack"
    GIVE_PROMPT_TO_EXTERNAL_AGENT = "give_prompt_to_external_agent"
    WAIT_FOR_EXTERNAL_IMPLEMENTATION = "wait_for_external_implementation"
    RUN_IMPLEMENTATION_INTAKE = "run_implementation_intake"
    HUMAN_REVIEW_MERGE_RECOMMENDATION = "human_review_merge_recommendation"
    PROVIDE_POST_MERGE_MANIFEST = "provide_post_merge_manifest"
    RUN_POST_MERGE_ASSIMILATION = "run_post_merge_assimilation"
    VALIDATE_RESEARCH_BASELINE = "validate_research_baseline"
    RUN_MINI_SOAK = "run_mini_soak"
    RUN_REPLICATION = "run_replication"
    RUN_FALSIFICATION = "run_falsification"
    START_NEXT_CYCLE = "start_next_cycle"
    RESOLVE_BLOCKER = "resolve_blocker"
    ARCHIVE_CYCLE = "archive_cycle"

    ALL = (REVIEW_CURRENT_BASELINE, RUN_ARCHITECTURE_EVOLUTION,
           COMPILE_EXPERIMENT_PACK, GIVE_PROMPT_TO_EXTERNAL_AGENT,
           WAIT_FOR_EXTERNAL_IMPLEMENTATION, RUN_IMPLEMENTATION_INTAKE,
           HUMAN_REVIEW_MERGE_RECOMMENDATION, PROVIDE_POST_MERGE_MANIFEST,
           RUN_POST_MERGE_ASSIMILATION, VALIDATE_RESEARCH_BASELINE,
           RUN_MINI_SOAK, RUN_REPLICATION, RUN_FALSIFICATION, START_NEXT_CYCLE,
           RESOLVE_BLOCKER, ARCHIVE_CYCLE)


class NextActionPriority:
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    ALL = (URGENT, HIGH, MEDIUM, LOW)


@dataclass
class ResearchCycleNextAction:
    """One recommended next operator action (instruction; never executed)."""

    action_type: str
    priority: str = NextActionPriority.MEDIUM
    detail: str = ""
    safety_context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"action_type": self.action_type, "priority": self.priority,
                "detail": self.detail, "safety_context": self.safety_context,
                "executed": False, "for_operator": True}


# stage -> (next action, priority, detail)
_STAGE_ACTION = {
    ResearchCycleStage.BASELINE_SELECTED: (
        NextActionType.REVIEW_CURRENT_BASELINE, NextActionPriority.MEDIUM,
        "review the current research baseline before proposing changes"),
    ResearchCycleStage.ROADMAP_DEFINED: (
        NextActionType.RUN_ARCHITECTURE_EVOLUTION, NextActionPriority.MEDIUM,
        "run the architecture evolution lab on the roadmap"),
    ResearchCycleStage.ARCHITECTURE_EVIDENCE_LOADED: (
        NextActionType.COMPILE_EXPERIMENT_PACK, NextActionPriority.MEDIUM,
        "compile an experiment pack from the architecture proposal"),
    ResearchCycleStage.VARIANT_PROPOSED: (
        NextActionType.COMPILE_EXPERIMENT_PACK, NextActionPriority.MEDIUM,
        "compile the experiment pack for the proposed variant"),
    ResearchCycleStage.EXPERIMENT_PACK_COMPILED: (
        NextActionType.GIVE_PROMPT_TO_EXTERNAL_AGENT, NextActionPriority.HIGH,
        "hand the IMPLEMENTATION_PROMPT to an external agent after operator "
        "approval"),
    ResearchCycleStage.WAITING_FOR_EXTERNAL_IMPLEMENTATION: (
        NextActionType.WAIT_FOR_EXTERNAL_IMPLEMENTATION,
        NextActionPriority.LOW,
        "wait for the external human/agent implementation artifact"),
    ResearchCycleStage.IMPLEMENTATION_SUBMITTED: (
        NextActionType.RUN_IMPLEMENTATION_INTAKE, NextActionPriority.HIGH,
        "run the implementation intake audit on the submitted artifacts"),
    ResearchCycleStage.IMPLEMENTATION_AUDITED: (
        NextActionType.HUMAN_REVIEW_MERGE_RECOMMENDATION,
        NextActionPriority.HIGH,
        "review the advisory merge recommendation; the human decides"),
    ResearchCycleStage.WAITING_FOR_HUMAN_MERGE: (
        NextActionType.PROVIDE_POST_MERGE_MANIFEST, NextActionPriority.MEDIUM,
        "after an external human merge, provide the post-merge manifest"),
    ResearchCycleStage.POST_MERGE_EVIDENCE_SUBMITTED: (
        NextActionType.RUN_POST_MERGE_ASSIMILATION, NextActionPriority.HIGH,
        "run post-merge assimilation on the supplied evidence"),
    ResearchCycleStage.POST_MERGE_ASSIMILATED: (
        NextActionType.VALIDATE_RESEARCH_BASELINE, NextActionPriority.MEDIUM,
        "build the research baseline from the assimilated candidate"),
    ResearchCycleStage.CANDIDATE_BASELINE_CREATED: (
        NextActionType.VALIDATE_RESEARCH_BASELINE, NextActionPriority.MEDIUM,
        "validate the candidate into a research baseline (operator decides)"),
    ResearchCycleStage.RESEARCH_BASELINE_VALIDATED: (
        NextActionType.RUN_MINI_SOAK, NextActionPriority.MEDIUM,
        "run a mini soak / replication / falsification on the new baseline"),
    ResearchCycleStage.SOAK_RECOMMENDED: (
        NextActionType.RUN_MINI_SOAK, NextActionPriority.MEDIUM,
        "run the recommended mini soak"),
    ResearchCycleStage.REPLICATION_RECOMMENDED: (
        NextActionType.RUN_REPLICATION, NextActionPriority.MEDIUM,
        "run the recommended replication"),
    ResearchCycleStage.FALSIFICATION_RECOMMENDED: (
        NextActionType.RUN_FALSIFICATION, NextActionPriority.MEDIUM,
        "run the recommended falsification replay"),
    ResearchCycleStage.ARCHITECTURE_EVOLUTION_RECOMMENDED: (
        NextActionType.RUN_ARCHITECTURE_EVOLUTION, NextActionPriority.MEDIUM,
        "feed the baseline into the next architecture-evolution cycle"),
    ResearchCycleStage.CYCLE_COMPLETE: (
        NextActionType.START_NEXT_CYCLE, NextActionPriority.LOW,
        "start the next research cycle from the validated baseline"),
    ResearchCycleStage.ARCHIVED: (
        NextActionType.ARCHIVE_CYCLE, NextActionPriority.LOW,
        "this cycle is archived; start a new cycle if desired"),
}

_HIGH_RISK = (NextActionType.GIVE_PROMPT_TO_EXTERNAL_AGENT,
              NextActionType.HUMAN_REVIEW_MERGE_RECOMMENDATION)


@dataclass
class NextActionPlanner:
    """Plans the next operator action (instructions only; never executed)."""

    def plan(self, *, stage: str, blocked: bool,
             blocked_states: Optional[List[Dict]] = None,
             ) -> List[ResearchCycleNextAction]:
        out: List[ResearchCycleNextAction] = []
        if blocked:
            for bs in (blocked_states or [{}]):
                rec = bs.get("recommendation", "resolve the blocker")
                out.append(ResearchCycleNextAction(
                    action_type=NextActionType.RESOLVE_BLOCKER,
                    priority=(NextActionPriority.URGENT
                              if bs.get("critical_safety")
                              else NextActionPriority.HIGH),
                    detail=f"resolve blocker: {bs.get('reason', 'unknown')} -> "
                           f"{rec}",
                    safety_context=("critical safety blocker -- cannot be "
                                    "bypassed" if bs.get("critical_safety")
                                    else "")))
            return out
        action_type, priority, detail = _STAGE_ACTION.get(
            stage, (NextActionType.REVIEW_CURRENT_BASELINE,
                    NextActionPriority.LOW, "review the current cycle state"))
        out.append(ResearchCycleNextAction(
            action_type=action_type, priority=priority, detail=detail,
            safety_context=("operator approval + safety gates required before "
                            "this action" if action_type in _HIGH_RISK
                            else "")))
        return out

    @staticmethod
    def summary(actions: List[ResearchCycleNextAction]) -> Dict[str, Any]:
        return {
            "next_action_count": len(actions),
            "actions": [a.to_dict() for a in actions],
            "executes_automatically": False,
            "note": "next actions are instructions for the human/operator; none "
                    "is executed automatically; if blocked, the next action is "
                    "blocker resolution",
        }
