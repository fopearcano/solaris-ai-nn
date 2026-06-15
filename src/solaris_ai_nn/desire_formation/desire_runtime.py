"""Desire-formation runtime -- bounded valence -> push -> desire -> safe action.

:class:`DesireFormationRuntime` reads the upstream operational states (metabolism,
cognition, self-boundary, plus optional LOGOS tension count), assesses valence,
forms pushes and desire candidates, builds the motivation field, detects conflicts,
evaluates readiness, arbitrates safely, executes only allowed *internal* actions,
and records outcomes. Everything is internal: no external action, no hardware/feeder/
source control, no unbounded loop, and no agency/free-will/emotion claims.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .arbitration import ArbitrationOutcome, DesireArbitrator
from .conflict import ConflictDetector
from .desire import DesireCandidate, DesireFormationEngine, DesireKind, \
    DesireStatus
from .desire_memory import DesireMemoryStore
from .internal_actions import InternalActionExecutor, InternalActionKind
from .motivation_field import MotivationField
from .outcome_trace import DesireOutcomeTrace, OutcomeType
from .push import PushFormationEngine
from .readiness import ReadinessGate, ReadinessState
from .reports import DesireFormationReportBuilder
from .safety import DesireFormationSafetyValidator
from .valence import ValenceAssessment


class DesireMilestone:
    FIRST_VALENCE = "first_valence_gradient"
    FIRST_PUSH = "first_push"
    FIRST_DESIRE = "first_desire_candidate"
    FIRST_CONFLICT = "first_desire_conflict"
    FIRST_INTERNAL_ACTION = "first_internal_action"
    FIRST_NO_OP = "first_no_op"
    FIRST_SAFETY_BLOCK = "first_safety_blocked_desire"
    FIRST_DEFERRED = "first_deferred_desire"
    FIRST_OUTCOME = "first_outcome_trace"

    ALL = (FIRST_VALENCE, FIRST_PUSH, FIRST_DESIRE, FIRST_CONFLICT,
           FIRST_INTERNAL_ACTION, FIRST_NO_OP, FIRST_SAFETY_BLOCK,
           FIRST_DEFERRED, FIRST_OUTCOME)


@dataclass
class DesireFormationRuntime:
    """The bounded valence/push/desire/arbitration loop (internal-only)."""

    state_dir: str = ".solaris_ai_nn_desire"
    sensorium: Any = None
    metabolism: Any = None
    ontogenesis: Any = None
    semiogenesis: Any = None
    cognition: Any = None
    self_boundary: Any = None
    max_pushes_per_tick: int = 50
    max_desires_per_tick: int = 50
    max_internal_actions_per_tick: int = 30
    max_runtime_s: float = 30.0
    max_ticks: int = 120
    dry_run: bool = False
    fixture_mode: bool = True
    live_read_only_mode: bool = False
    governance_ok: bool = True

    valence_assessor: ValenceAssessment = field(
        default_factory=ValenceAssessment)
    push_engine: PushFormationEngine = field(
        default_factory=PushFormationEngine)
    desire_engine: DesireFormationEngine = field(
        default_factory=DesireFormationEngine)
    motivation: MotivationField = field(default_factory=MotivationField)
    conflict_detector: ConflictDetector = field(
        default_factory=ConflictDetector)
    readiness_gate: ReadinessGate = field(default_factory=ReadinessGate)
    arbitrator: DesireArbitrator = field(default_factory=DesireArbitrator)
    executor: InternalActionExecutor = field(
        default_factory=InternalActionExecutor)
    outcomes: DesireOutcomeTrace = field(default_factory=DesireOutcomeTrace)
    memory: DesireMemoryStore = field(default=None, init=False)
    safety: DesireFormationSafetyValidator = field(
        default_factory=DesireFormationSafetyValidator)

    desires: List[DesireCandidate] = field(default_factory=list, init=False)
    milestones: List[str] = field(default_factory=list, init=False)
    ticks_run: int = field(default=0, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.memory = DesireMemoryStore(state_dir=self.state_dir,
                                        persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    def _milestone(self, name: str) -> None:
        if name not in self.milestones:
            self.milestones.append(name)

    def _status(self, component: Any, method: str) -> Dict[str, Any]:
        if component is None:
            return {}
        if isinstance(component, dict):
            return component
        if hasattr(component, method):
            return getattr(component, method)()
        if hasattr(component, "snapshot"):
            return component.snapshot()
        return {}

    def _logos_tension_count(self) -> int:
        for c in (self.cognition, self.self_boundary):
            if c is not None and hasattr(c, "logos_tensions"):
                try:
                    return len(c.logos_tensions())
                except Exception:
                    continue
        return 0

    def update(self, *, tick: int = 0,
               extra_desires: Optional[List[DesireCandidate]] = None,
               ) -> Dict[str, Any]:
        """Run one bounded desire-formation tick."""
        if self._refused:
            return {"refused": True, "reason": "unbounded desire loop"}
        self.ticks_run += 1
        metabolism = self._status(self.metabolism, "metabolism_status")
        cognition = self._status(self.cognition, "cognition_status")
        boundary = self._status(self.self_boundary, "self_boundary_status")
        overloaded = bool(metabolism.get("overload_state"))

        # 1. Valence.
        gradient = self.valence_assessor.assess(
            metabolism=metabolism, cognition=cognition, self_boundary=boundary,
            logos_tension_count=self._logos_tension_count())
        for v in gradient.valences:
            self.memory.record_valence(v.to_dict())
        if gradient.valences:
            self._milestone(DesireMilestone.FIRST_VALENCE)

        # 2. Pushes.
        pushes = self.push_engine.form(gradient,
                                       max_pushes=self.max_pushes_per_tick)
        for p in pushes:
            self.memory.record_push(p.to_dict())
        if pushes:
            self._milestone(DesireMilestone.FIRST_PUSH)

        # 3. Desires.
        self.desires = self.desire_engine.form(
            pushes, max_desires=self.max_desires_per_tick)
        if extra_desires:
            self.desires.extend(extra_desires)
        if self.desires:
            self._milestone(DesireMilestone.FIRST_DESIRE)

        # 4. Conflicts.
        conflicts = self.conflict_detector.detect(self.desires)
        if conflicts:
            self._milestone(DesireMilestone.FIRST_CONFLICT)

        # 5. Readiness + arbitration + execution per desire.
        boundary_clear = float(
            boundary.get("boundary_confidence_score", 1.0) or 1.0) >= 0.4
        energy_ok = not overloaded
        attention_ok = not overloaded
        actions_done = 0
        for desire in self.desires:
            # Safety check on the desire's intended internal action.
            action_kind = getattr(desire, "expected_internal_action", "no_op")
            safe = self.safety.validate_internal_action(action_kind).safe
            readiness = self.readiness_gate.evaluate(
                desire, energy_ok=energy_ok, attention_ok=attention_ok,
                boundary_clear=boundary_clear, safety_ok=safe,
                governance_ok=self.governance_ok)
            result = self.arbitrator.arbitrate(
                desire, readiness, overloaded=overloaded, safety_ok=safe)
            self._apply(desire, result, action_kind, actions_done)
            if result.outcome in (ArbitrationOutcome.SELECT_INTERNAL_ACTION,
                                  ArbitrationOutcome.SELECT_SIMULATION,
                                  ArbitrationOutcome.SELECT_ATTENTION_SHIFT,
                                  ArbitrationOutcome.SELECT_CONSOLIDATION):
                actions_done += 1
            self.memory.record_desire(desire.to_dict())

        self.motivation.build(pushes, self.desires, valence_gradient=gradient)
        for o in self.outcomes.outcomes:
            self.memory.record_outcome(o.to_dict())
        if self.outcomes.outcomes:
            self._milestone(DesireMilestone.FIRST_OUTCOME)
        self.memory.write_index()

        self._last = {
            "tick": tick,
            "valence_gradient_count": len(gradient.valences),
            "push_count": len(pushes),
            "desire_candidate_count": len(self.desires),
            "conflict_count": len(conflicts),
            "internal_action_count": len(self.executor.executed),
            "no_op_count": self.executor.no_op_count,
        }
        return self._last

    def _apply(self, desire: Any, result: Any, action_kind: str,
               actions_done: int) -> None:
        outcome_type = OutcomeType.UNKNOWN
        oc = result.outcome
        if oc == ArbitrationOutcome.SAFETY_BLOCK:
            desire.status = DesireStatus.BLOCKED_BY_SAFETY
            self.conflict_detector.add_safety_conflict(desire.desire_id)
            outcome_type = OutcomeType.DESIRE_SAFETY_BLOCKED
            self._milestone(DesireMilestone.FIRST_SAFETY_BLOCK)
        elif oc == ArbitrationOutcome.GOVERNANCE_BLOCK:
            desire.status = DesireStatus.DEFERRED
            self.conflict_detector.add_governance_conflict(desire.desire_id)
            outcome_type = OutcomeType.DESIRE_GOVERNANCE_BLOCKED
        elif oc == ArbitrationOutcome.NO_OP:
            desire.status = (DesireStatus.SATISFIED
                             if desire.kind == DesireKind.NO_ACTION
                             else DesireStatus.INHIBITED)
            self.executor.execute(InternalActionKind.NO_OP, desire.desire_id)
            outcome_type = OutcomeType.NO_ACTION_TAKEN
            self._milestone(DesireMilestone.FIRST_NO_OP)
        elif oc == ArbitrationOutcome.INHIBIT:
            desire.status = DesireStatus.INHIBITED
            outcome_type = OutcomeType.DESIRE_INHIBITED
        elif oc == ArbitrationOutcome.DEFER:
            desire.status = DesireStatus.DEFERRED
            outcome_type = OutcomeType.DESIRE_DEFERRED
            self._milestone(DesireMilestone.FIRST_DEFERRED)
        else:
            # A selected internal action (within the per-tick action cap).
            if actions_done >= self.max_internal_actions_per_tick:
                desire.status = DesireStatus.DEFERRED
                outcome_type = OutcomeType.DESIRE_DEFERRED
            else:
                action = self.executor.execute(
                    result.selected_action or action_kind, desire.desire_id)
                self.memory.record_internal_action(action.to_dict())
                desire.status = DesireStatus.SATISFIED
                outcome_type = OutcomeType.INTERNAL_ACTION_COMPLETED
                self._milestone(DesireMilestone.FIRST_INTERNAL_ACTION)
        self.outcomes.record(outcome_type, desire.desire_id,
                             selected_action_refs=[result.selected_action]
                             if result.selected_action else [],
                             outcome_evidence=[result.reason])

    def run_bounded(self, max_ticks: Optional[int] = None) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True}
        started = time.time()
        n = min(self.max_ticks, max_ticks or self.max_ticks)
        for tick in range(n):
            if time.time() - started > self.max_runtime_s:
                break
            self.update(tick=tick)
        return {"refused": False, "ticks_run": self.ticks_run,
                "last": self._last}

    # -- integration views ----------------------------------------------------

    def latent_replay_recommendations(self) -> List[str]:
        recs: List[str] = []
        for d in self.desires:
            if d.status in (DesireStatus.FAILED, DesireStatus.BLOCKED_BY_SAFETY,
                            DesireStatus.INHIBITED):
                recs.append(f"replay_desire:{d.desire_id}:{d.status}")
            if len(recs) >= 6:
                break
        return recs

    def logos_tensions(self) -> List[Any]:
        """Desire conflicts expressed as LOGOS tensions (valid types only)."""
        from ..logos_complexity.tension import (
            LogosTension,
            TensionPolarity,
            TensionType,
        )

        tensions: List[LogosTension] = []
        for c in self.conflict_detector.conflicts:
            if c.conflict_type == "safety_vs_desire":
                ltype, pa, pb = (TensionType.NEED_SAFETY,
                                 TensionPolarity.NEED, TensionPolarity.SAFETY)
            elif c.conflict_type == "novelty_vs_stability":
                ltype, pa, pb = (TensionType.EXPLORE_STABILIZE,
                                 TensionPolarity.EXPLORE,
                                 TensionPolarity.STABILIZE)
            elif c.conflict_type == "act_now_vs_wait":
                ltype, pa, pb = (TensionType.ACTION_INHIBITION,
                                 TensionPolarity.ACTION,
                                 TensionPolarity.INHIBITION)
            else:
                ltype, pa, pb = (TensionType.EXPLORE_STABILIZE,
                                 TensionPolarity.EXPLORE,
                                 TensionPolarity.STABILIZE)
            tensions.append(LogosTension(
                tension_type=ltype, polarity_a=pa, polarity_b=pb,
                source_modules=["desire_formation"],
                metadata={"desire_conflict": c.conflict_type}))
        return tensions

    def hypothesis_seeds(self) -> List[Any]:
        """Test-prediction / inspect / compare desires seed hypotheses."""
        from ..hypothesis.sources import HypothesisSeed

        seeds: List[HypothesisSeed] = []
        for d in self.desires:
            if d.kind in (DesireKind.TEST_PREDICTION, DesireKind.INSPECT_ABSENCE,
                          DesireKind.COMPARE_MODALITIES,
                          DesireKind.MARK_SOURCE_UNRELIABLE):
                seeds.append(HypothesisSeed(
                    source="desire_formation", hypothesis_type="relation",
                    target_ref=d.desire_id,
                    observation=f"desire {d.kind} -> {d.expected_internal_action}",
                    intensity=d.expected_utility,
                    evidence_refs=list(d.evidence_refs)))
        return seeds

    def desire_status(self) -> Dict[str, Any]:
        ds = self.desires
        return {
            "desire_formation_enabled": True,
            "valence_gradient_count": len(self.valence_assessor.gradient.valences),
            "push_count": len(self.push_engine.pushes),
            "desire_candidate_count": len(ds),
            "active_desire_count": sum(
                1 for d in ds if d.status in (DesireStatus.CANDIDATE,
                                              DesireStatus.ACTIVE)),
            "inhibited_desire_count": sum(
                1 for d in ds if d.status == DesireStatus.INHIBITED),
            "deferred_desire_count": sum(
                1 for d in ds if d.status == DesireStatus.DEFERRED),
            "satisfied_desire_count": sum(
                1 for d in ds if d.status == DesireStatus.SATISFIED),
            "failed_desire_count": sum(
                1 for d in ds if d.status == DesireStatus.FAILED),
            "safety_blocked_desire_count": sum(
                1 for d in ds if d.status == DesireStatus.BLOCKED_BY_SAFETY),
            "governance_blocked_desire_count": sum(
                1 for r in self.arbitrator.results
                if r.outcome == ArbitrationOutcome.GOVERNANCE_BLOCK),
            "internal_action_count": len(self.executor.executed),
            "no_op_count": self.executor.no_op_count,
            "desire_conflict_count": len(self.conflict_detector.conflicts),
            "desire_outcome_success_rate": self.outcomes.success_rate(),
            "dominant_valence_direction":
                self.valence_assessor.gradient.dominant_direction(),
            "motivation_field": self.motivation.state.to_dict(),
            "latest_desire_formation_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "DESIRE_FORMATION_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.desire_status()

    def write_artifacts(self) -> Dict[str, Any]:
        return DesireFormationReportBuilder(self).write()
