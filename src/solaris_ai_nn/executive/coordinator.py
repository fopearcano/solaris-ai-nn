"""ExecutiveLayer -- the wired pipeline from Desire candidates to one
suggestion.

One ``decide(candidates, context)``: mode is determined (ops first), the
desires queue up, inhibition runs across queue and action candidates,
prospection estimates consequences, arbitration scores everything with the
penalties dominating, optionally a short plan is built, and the whole
decision -- selected, rejected, inhibited, reasons -- lands in the decision
trace. The output is a suggestion. Always.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .action_candidates import (
    ActionCandidate,
    ActionCandidateSet,
    ActionCandidateType,
    ExecutableScope,
    candidate_from_desire,
)
from .arbitration import ActionArbitrator, ArbitrationResult
from .attention import AttentionSelector
from .decision_trace import DecisionTraceRecorder
from .desire_queue import DesireQueue
from .inhibition import InhibitionController
from .planner import ShortHorizonPlanner
from .policy import ExecutiveMode, ExecutivePolicy
from .prospection import ProspectionEngine
from .safety import ExecutiveSafetyValidator
from .working_memory import WorkingMemory


@dataclass
class ExecutiveLayer:
    """Owns the executive pipeline; produces suggestions, never actions."""

    state_dir: Optional[Union[str, Path]] = None
    mode: str = ExecutiveMode.DEFAULT
    max_plan_length: int = 3
    # Optional ego/self-model (Prompt 18): consulted for action authority,
    # perspective, and boundary status. It can only inhibit, never permit.
    ego: Optional[Any] = None

    def __post_init__(self) -> None:
        self.policy = ExecutivePolicy(requested_mode=self.mode)
        self.queue = DesireQueue()
        self.inhibition = InhibitionController()
        self.arbitrator = ActionArbitrator()
        self.prospection = ProspectionEngine()
        self.safety = ExecutiveSafetyValidator()
        self.planner = ShortHorizonPlanner(
            max_plan_length=self.max_plan_length, safety=self.safety,
            inhibition=self.inhibition, prospection=self.prospection)
        self.memory = WorkingMemory()
        self.attention = AttentionSelector()
        self.recorder = DecisionTraceRecorder(state_dir=self.state_dir)
        self.decisions = 0
        self.no_safe_action_total = 0
        self.last_result: Optional[ArbitrationResult] = None
        self.last_plan = None
        self.last_focus = None

    # -- the pipeline ---------------------------------------------------------------

    def decide(self, desire_candidates: List[Any],
               context: Optional[Dict[str, Any]] = None,
               readout_suggestion: Optional[str] = None,
               step: int = 0, record: bool = True) -> ArbitrationResult:
        ctx = dict(context or {})
        mode = self.policy.determine_mode(ctx)
        self.memory.set_mode(mode)
        focus = self.attention.select_focus(ctx)
        self.last_focus = focus
        self.memory.set_focus(focus.to_dict())

        # 1. Queue the desires; inhibition sweeps the queue.
        self.queue.remove_expired()
        self.queue.push_many(desire_candidates or [])
        self.inhibition.apply_to_queue(self.queue, ctx)

        # 2. Desires (and the raw readout suggestion) become candidates.
        candidates: List[ActionCandidate] = []
        for queued in self.queue.peek(limit=10):
            candidate = candidate_from_desire(
                queued.candidate
                if queued.candidate is not None else queued)
            candidate.inhibited = queued.inhibited
            candidate.inhibition_reason = queued.inhibition_reason
            candidate.metadata["urgency"] = queued.urgency
            candidates.append(candidate)
        if readout_suggestion:
            candidates.append(ActionCandidate(
                action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                label=str(readout_suggestion),
                expected_effect="the readout's standing tendency",
                expected_cost=0.2, confidence=0.5, utility_estimate=0.3,
                executable_scope=ExecutableScope.SIMULATION_ONLY,
                metadata={"source": "readout"}))
        candidate_set = ActionCandidateSet(candidates=candidates)

        # 3. Mode gating + safety + inhibition over the action candidates.
        for candidate in candidate_set.candidates:
            if candidate.inhibited:
                continue
            if not self.policy.allows(candidate.action_type):
                candidate.inhibited = True
                candidate.inhibition_reason = (
                    f"executive mode {mode!r} does not permit "
                    f"{candidate.action_type}")
                continue
            report = self.safety.validate_candidate(candidate, ctx)
            if not report.safe:
                candidate.inhibited = True
                candidate.inhibition_reason = report.violations[0]
        self.inhibition.apply_to_candidates(candidate_set.candidates, ctx)

        # 3b. Ego/self-model boundary gate (Prompt 18): the self-model can
        # add inhibitions (forbidden boundary crossings) but never remove
        # one or grant authority the policy/safety layers withheld.
        if self.ego is not None:
            ctx.setdefault("ego_perspective",
                           self.ego.perspective.state.mode)
            ctx.setdefault("ego_action_authority",
                           self.ego.action_authority())
            ctx.setdefault("ego_boundary_violations",
                           self.ego.boundaries.violations_total)
            for candidate in candidate_set.candidates:
                if candidate.inhibited:
                    continue
                ok, why = self.ego.check_action_boundary(
                    candidate.label, candidate.action_type,
                    bool(candidate.committed))
                if not ok:
                    candidate.inhibited = True
                    candidate.inhibition_reason = f"ego_boundary: {why}"

        # 4. Prospection over the survivors feeds the arbitration context.
        prospection = self.prospection.compare_candidates(
            candidate_set.active(), ctx)
        ctx["prospection"] = prospection

        # 5. Arbitrate (penalties dominate; fallback never forces).
        result = self.arbitrator.select(candidate_set.candidates, ctx)
        selection_report = self.safety.validate_selection(result.selected,
                                                          ctx)
        if not selection_report.safe:
            from .action_candidates import no_action_candidate

            result.selected = no_action_candidate(
                selection_report.violations[0])
            result.fallback_used = True
        if result.fallback_used:
            self.no_safe_action_total += 1

        # 6. Optional short plan (only in short_plan mode).
        self.last_plan = None
        if self.policy.planning_allowed() and result.selected is not None \
                and result.selected.action_type \
                != ActionCandidateType.NO_ACTION:
            plan = self.planner.build_plan(result.selected.label, ctx)
            if not plan.rejected:
                self.planner.evaluate_plan(plan, ctx)
            self.last_plan = plan

        # 7. Working memory + the decision trace.
        self.memory.add("decision", {"selected": (result.selected.label
                                                  if result.selected
                                                  else None),
                                     "fallback": result.fallback_used})
        if record:
            self.recorder.record_decision(
                step=step, mode=mode, queue=self.queue,
                candidates=candidate_set, result=result,
                prospection=prospection,
                context_summary={"focus": focus.target,
                                 "health": ctx.get("health_level"),
                                 "latent_mode": ctx.get("latent_mode")})
        self.decisions += 1
        self.last_result = result
        return result

    # -- persistence / status ---------------------------------------------------------

    def save_state(self) -> None:
        self.recorder.save_state(
            self.snapshot(),
            plan=(self.last_plan.to_dict() if self.last_plan else None))

    def summary(self) -> Dict[str, Any]:
        """Compact executive status for the Inner MAP / supervisor."""
        result = self.last_result
        selected = (result.selected.label
                    if result and result.selected else None)
        last_score = None
        if result and result.scores:
            best = result.scores[0]
            last_score = {"label": best.candidate.label,
                          "total": round(best.total, 4),
                          "blocked": best.blocked}
        prospection_confidences = [r.get("confidence", 0.0)
                                   for r in
                                   self.prospection.last_results[-5:]]
        return {
            "enabled": True,
            "mode": self.policy.mode,
            "active_focus": (self.last_focus.target
                             if self.last_focus else None),
            "desire_queue_length": len(self.queue),
            "candidate_count": (len(result.scores) if result else 0),
            "inhibited_candidate_count": self.inhibition.inhibitions_total,
            "selected_action_suggestion": selected,
            "selected_plan_length": (len(self.last_plan.live_steps())
                                     if self.last_plan
                                     and not self.last_plan.rejected
                                     else 0),
            "no_safe_action_count": self.no_safe_action_total,
            "last_arbitration_score": last_score,
            "last_prospection_confidence": (
                round(sum(prospection_confidences)
                      / len(prospection_confidences), 4)
                if prospection_confidences else None),
            "decisions": self.decisions,
            "fallback_total": self.arbitrator.fallback_total,
            "plans_rejected": self.planner.plans_rejected,
            "forced_emergency_total": self.policy.forced_emergency_total,
            "decision_trace_path": (str(self.recorder.trace_path)
                                    if self.recorder.trace_path else None),
            "executive_report_path": None,  # set by callers that save one
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "policy": self.policy.snapshot(),
            "queue": self.queue.snapshot(),
            "inhibition": self.inhibition.snapshot(),
            "arbitration": self.arbitrator.snapshot(),
            "prospection": self.prospection.snapshot(),
            "planner": self.planner.snapshot(),
            "working_memory": self.memory.snapshot(),
            "attention": self.attention.snapshot(),
            "decision_trace": self.recorder.snapshot(),
            "safety": self.safety.snapshot(),
        }
