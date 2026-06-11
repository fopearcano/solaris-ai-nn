"""ShortHorizonPlanner -- tiny suggestion-only plans, refused beyond bounds.

Plans are built from fixed templates (rest -> look, avoid_danger -> rest,
checkpoint_now -> consolidate_memory, ...), capped at 3 steps by default and
5 absolutely (unless governance explicitly permits longer -- it does not, by
default). Every step is safety/inhibition checked; blocked steps stay in the
plan, marked. Long-horizon autonomous planning is structurally refused.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
    PROPOSAL_TO_CANDIDATE,
)
from .inhibition import InhibitionController
from .prospection import ProspectionEngine, ProspectionResult
from .safety import (
    DEFAULT_MAX_PLAN_LENGTH,
    HARD_MAX_PLAN_LENGTH,
    ExecutiveSafetyValidator,
)

# goal/desire proposal -> short step template.
PLAN_TEMPLATES: Dict[str, List[str]] = {
    "rest": ["rest", "look"],
    "look": ["look"],
    "seek_signal": ["seek_signal", "emit_ping"],
    "avoid_danger": ["avoid_danger", "rest"],
    "approach_reward": ["look", "approach_reward"],
    "explore_safely": ["look", "explore_safely", "rest"],
    "checkpoint_now": ["checkpoint_now", "consolidate_memory"],
    "consolidate_memory": ["consolidate_memory"],
    "run_replay": ["run_replay", "consolidate_memory"],
    "reduce_activity": ["reduce_activity", "rest"],
    "stabilize": ["stabilize"],
    "remain_observe_only": ["remain_observe_only", "no_action"],
    "request_operator_review": ["request_operator_review", "no_action"],
    "safe_shutdown_recommended": ["checkpoint_now",
                                  "safe_shutdown_recommended"],
}


@dataclass
class PlanStep:
    """One suggested step (a suggestion, never an executed act)."""

    index: int
    label: str
    blocked: bool = False
    blocked_reason: str = ""
    suggestion_only: bool = True  # structurally: always

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ActionPlan:
    """A short, bounded, suggestion-only plan."""

    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    prospection: Optional[Dict[str, Any]] = None
    rejected: bool = False
    rejected_reason: str = ""
    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    created_at: float = field(default_factory=time.time)

    def live_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if not s.blocked]

    def blocked_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if s.blocked]

    def __len__(self) -> int:
        return len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id, "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "live_steps": [s.label for s in self.live_steps()],
            "blocked_steps": [{"label": s.label, "reason": s.blocked_reason}
                              for s in self.blocked_steps()],
            "prospection": self.prospection,
            "rejected": self.rejected,
            "rejected_reason": self.rejected_reason,
            "created_at": self.created_at,
            "note": "plans are suggestions only; nothing executes them by "
                    "itself",
        }


@dataclass
class ShortHorizonPlanner:
    """Builds, evaluates, and selects bounded suggestion-only plans."""

    max_plan_length: int = DEFAULT_MAX_PLAN_LENGTH
    safety: ExecutiveSafetyValidator = field(
        default_factory=ExecutiveSafetyValidator)
    inhibition: InhibitionController = field(
        default_factory=InhibitionController)
    prospection: ProspectionEngine = field(default_factory=ProspectionEngine)

    plans_built: int = field(default=0, init=False)
    plans_rejected: int = field(default=0, init=False)
    last_plan: Optional[ActionPlan] = field(default=None, init=False)

    def build_plan(self, goal_or_desire: Any,
                   context: Optional[Dict[str, Any]] = None) -> ActionPlan:
        ctx = dict(context or {})
        goal = getattr(goal_or_desire, "proposal",
                       getattr(goal_or_desire, "label",
                               str(goal_or_desire)))
        template = PLAN_TEMPLATES.get(goal, [goal])
        limit = (HARD_MAX_PLAN_LENGTH
                 if ctx.get("governance_allows_long_plans")
                 else min(self.max_plan_length, HARD_MAX_PLAN_LENGTH))
        plan = ActionPlan(goal=goal)
        if len(template) > limit:
            template = template[:limit]
        for index, label in enumerate(template, start=1):
            step = PlanStep(index=index, label=label)
            action_type, scope = PROPOSAL_TO_CANDIDATE.get(
                label, (ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
                        ExecutableScope.INTERNAL_ONLY))
            probe = ActionCandidate(action_type=action_type, label=label,
                                    executable_scope=scope)
            safety_report = self.safety.validate_candidate(probe, ctx)
            if not safety_report.safe:
                step.blocked = True
                step.blocked_reason = safety_report.violations[0]
            else:
                inhibition = self.inhibition.evaluate_action(probe, ctx)
                if inhibition.inhibited:
                    step.blocked = True
                    step.blocked_reason = (f"{inhibition.rule_id}: "
                                           f"{inhibition.reason}")
            plan.steps.append(step)

        plan_report = self.safety.validate_plan(plan, ctx)
        if not plan_report.safe:
            plan.rejected = True
            plan.rejected_reason = plan_report.violations[0]
            self.plans_rejected += 1
        elif not plan.live_steps():
            plan.rejected = True
            plan.rejected_reason = ("every step was blocked; the plan has "
                                    "nothing safe to suggest")
            self.plans_rejected += 1
        self.plans_built += 1
        self.last_plan = plan
        return plan

    def evaluate_plan(self, plan: ActionPlan,
                      context: Optional[Dict[str, Any]] = None,
                      ) -> ProspectionResult:
        result = self.prospection.simulate_sequence(plan.live_steps(),
                                                    context)
        plan.prospection = result.to_dict()
        return result

    def select_plan(self, plans: List[ActionPlan],
                    context: Optional[Dict[str, Any]] = None,
                    ) -> Optional[ActionPlan]:
        """The viable plan with the best prospection estimate."""
        viable = [p for p in plans if not p.rejected and p.live_steps()]
        if not viable:
            return None
        scored = []
        for plan in viable:
            result = self.evaluate_plan(plan, context)
            score = ((result.expected_valence or 0.0)
                     - result.expected_risk - 0.1 * result.expected_cost)
            scored.append((score, plan.goal, plan))
        scored.sort(key=lambda row: (-row[0], row[1]))
        selected = scored[0][2]
        self.last_plan = selected
        return selected

    def snapshot(self) -> Dict[str, Any]:
        return {
            "plans_built": self.plans_built,
            "plans_rejected": self.plans_rejected,
            "max_plan_length": self.max_plan_length,
            "hard_max": HARD_MAX_PLAN_LENGTH,
            "last_plan": (self.last_plan.to_dict()
                          if self.last_plan else None),
        }
