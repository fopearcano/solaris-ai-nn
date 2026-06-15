"""Action-reaction runtime -- close the loop: action -> reaction -> learning.

:class:`ActionReactionRuntime` reads the internal actions selected by desire
formation, validates their scope, generates reactions, builds consequence traces,
learns provisional effects, forms/weakens habits, records inhibitions, and updates
an internal action policy. Everything is internal/simulated/report-only: no
external actuation, no hardware/feeder/source control, and a strictly bounded loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_model import (
    ActionCandidateRecord,
    ActionExecutionStatus,
    ActionKind,
    ActionScope,
)
from .action_policy import ActionPolicyEngine
from .consequence import (
    ConsequenceTrace,
    ConsequenceWindow,
    consequence_type_for_reaction,
)
from .effect_learning import EffectLearningEngine
from .habit_formation import HabitFormationEngine, HabitTrigger
from .inhibition import InhibitionEngine, InhibitionReason
from .reaction import ReactionAssessment, ReactionKind, ReactionValence
from .reaction_memory import ReactionMemoryStore
from .reports import ActionReactionReportBuilder
from .safety import ActionReactionSafetyValidator


class ActionReactionMilestone:
    FIRST_ACTION = "first_selected_action"
    FIRST_REACTION = "first_reaction"
    FIRST_CONSEQUENCE = "first_consequence_trace"
    FIRST_EFFECT = "first_learned_effect"
    FIRST_HABIT = "first_habit_candidate"
    FIRST_INHIBITION = "first_inhibition"
    FIRST_NO_EFFECT = "first_no_effect_action"
    FIRST_BLOCK = "first_blocked_action"
    FIRST_POLICY_UPDATE = "first_policy_update"

    ALL = (FIRST_ACTION, FIRST_REACTION, FIRST_CONSEQUENCE, FIRST_EFFECT,
           FIRST_HABIT, FIRST_INHIBITION, FIRST_NO_EFFECT, FIRST_BLOCK,
           FIRST_POLICY_UPDATE)


# Maps an action kind onto the habit trigger that tends to evoke it.
_ACTION_TRIGGER = {
    ActionKind.INSPECT_ABSENCE_WINDOW: HabitTrigger.SOURCE_SILENCE_REPEATS,
    ActionKind.COMPARE_MODALITIES: HabitTrigger.SIGN_DRIFT_RISES,
    ActionKind.NO_OP: HabitTrigger.OVERLOAD_RISES,
    ActionKind.PRESERVE_UNKNOWN: HabitTrigger.PREDICTION_FAILS_REPEATEDLY,
    ActionKind.SHIFT_ATTENTION: HabitTrigger.MODALITY_IGNORED_TOO_LONG,
    ActionKind.MARK_SOURCE_UNRELIABLE: HabitTrigger.LABEL_CONTAMINATION_RISES,
}

_CONSTRUCTIVE = frozenset({ReactionValence.CONSTRUCTIVE,
                           ReactionValence.STABILIZING})


@dataclass
class ActionReactionRuntime:
    """The bounded closed action-reaction loop (internal-only)."""

    state_dir: str = ".solaris_ai_nn_action_reaction"
    desire: Any = None
    metabolism: Any = None
    cognition: Any = None
    self_boundary: Any = None
    max_actions_per_tick: int = 60
    max_runtime_s: float = 30.0
    max_ticks: int = 120
    effect_window_ticks: int = 3
    dry_run: bool = False
    fixture_mode: bool = True
    live_read_only_mode: bool = False

    reaction_assessor: ReactionAssessment = field(
        default_factory=ReactionAssessment)
    effect_engine: EffectLearningEngine = field(
        default_factory=EffectLearningEngine)
    habit_engine: HabitFormationEngine = field(
        default_factory=HabitFormationEngine)
    inhibition_engine: InhibitionEngine = field(
        default_factory=InhibitionEngine)
    policy_engine: ActionPolicyEngine = field(
        default_factory=ActionPolicyEngine)
    memory: ReactionMemoryStore = field(default=None, init=False)
    safety: ActionReactionSafetyValidator = field(
        default_factory=ActionReactionSafetyValidator)

    actions: List[ActionCandidateRecord] = field(default_factory=list,
                                                 init=False)
    reactions: List[Any] = field(default_factory=list, init=False)
    consequences: List[Any] = field(default_factory=list, init=False)
    milestones: List[str] = field(default_factory=list, init=False)
    ticks_run: int = field(default=0, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.memory = ReactionMemoryStore(state_dir=self.state_dir,
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

    def _selected_actions(self) -> List[ActionCandidateRecord]:
        """Read the internal actions selected by desire formation."""
        out: List[ActionCandidateRecord] = []
        desire = self.desire
        executed = []
        if desire is not None and hasattr(desire, "executor"):
            executed = list(getattr(desire.executor, "executed", []))
        elif isinstance(desire, (list, tuple)):
            executed = list(desire)
        for a in executed:
            out.append(ActionCandidateRecord(
                kind=getattr(a, "kind", "no_op"),
                desire_ref=getattr(a, "desire_ref", ""),
                evidence_refs=[getattr(a, "action_id", "")]))
        return out

    def update(self, *, tick: int = 0,
               extra_actions: Optional[List[ActionCandidateRecord]] = None,
               no_effect: bool = False) -> Dict[str, Any]:
        """Run one bounded closed-loop tick over the selected internal actions."""
        if self._refused:
            return {"refused": True, "reason": "unbounded action loop"}
        self.ticks_run += 1
        metabolism = self._status(self.metabolism, "metabolism_status")
        boundary = self._status(self.self_boundary, "self_boundary_status")

        candidates = self._selected_actions()
        if extra_actions:
            candidates.extend(extra_actions)
        candidates = candidates[:self.max_actions_per_tick]

        before = {"uncertainty": float(
            boundary.get("source_attribution_uncertainty_score", 0.5) or 0.5)}
        overloaded = bool(metabolism.get("overload_state"))

        for action in candidates:
            self._milestone(ActionReactionMilestone.FIRST_ACTION)
            # 1. Scope / safety validation.
            scope_ok = self.safety.validate_action_scope(action.scope).safe
            if action.is_forbidden or not scope_ok:
                action.status = ActionExecutionStatus.BLOCKED
                action.scope = ActionScope.FORBIDDEN_EXTERNAL
                self.memory.record_action(action.to_dict())
                reaction = self._reaction(
                    ReactionKind.BLOCKED_BY_SAFETY, action,
                    valence=ReactionValence.NEUTRAL)
                self.inhibition_engine.inhibit(
                    InhibitionReason.SAFETY_RISK, action_ref=action.action_id,
                    action_kind=action.kind, evidence_refs=["forbidden_scope"])
                self._milestone(ActionReactionMilestone.FIRST_BLOCK)
                self._milestone(ActionReactionMilestone.FIRST_INHIBITION)
                self._consequence(action, reaction, before, before, tick)
                continue
            self.actions.append(action)
            self.memory.record_action(action.to_dict())

            # 2. Reaction (no-effect path can be forced for the demo/test).
            if no_effect:
                reaction = self._reaction(ReactionKind.NO_EFFECT, action,
                                          valence=ReactionValence.NEUTRAL)
                self._milestone(ActionReactionMilestone.FIRST_NO_EFFECT)
                after = dict(before)
            else:
                # Only attention/inspect-style actions reduce the uncertainty
                # proxy; other actions yield their specific expected reaction
                # (concept/sign/metabolic/boundary change) via the assessor.
                after = dict(before)
                expected = self.reaction_assessor.expected_reaction(action.kind)
                if expected == ReactionKind.UNCERTAINTY_REDUCED:
                    after["uncertainty"] = round(
                        max(0.0, before["uncertainty"] - 0.1), 4)
                reaction_obj = self.reaction_assessor.assess(
                    action, before=before, after=after)
                reaction = reaction_obj
                self.reactions.append(reaction)
                self.memory.record_reaction(reaction.to_dict())
                self._milestone(ActionReactionMilestone.FIRST_REACTION)

            # 3. Consequence trace.
            self._consequence(action, reaction, before, after, tick)

            # 4. Effect learning.
            res = self.effect_engine.observe(action.kind, reaction.kind,
                                             reaction.valence)
            self.memory.record_effect(
                self.effect_engine.models[action.kind].to_dict())
            if self.effect_engine.learned_count():
                self._milestone(ActionReactionMilestone.FIRST_EFFECT)

            # 5. Habit reinforcement / weakening.
            trigger = _ACTION_TRIGGER.get(action.kind)
            if trigger is not None:
                if reaction.valence in _CONSTRUCTIVE:
                    habit = self.habit_engine.reinforce(
                        trigger, evidence_ref=action.action_id)
                else:
                    habit = self.habit_engine.weaken(trigger)
                # A boundary-uncertain habit toward simulation is inhibited.
                if overloaded and action.kind == ActionKind.RUN_BOUNDED_SIMULATION:
                    self.habit_engine.inhibit(trigger)
                self.memory.record_habit(habit.to_dict())
                self._milestone(ActionReactionMilestone.FIRST_HABIT)

        # 6. Policy update from accumulated effects.
        updates = self.policy_engine.update_from_effects(self.effect_engine,
                                                         self.habit_engine)
        for u in updates:
            self.memory.record_policy_update(u.to_dict())
        if updates:
            self._milestone(ActionReactionMilestone.FIRST_POLICY_UPDATE)
        for inh in self.inhibition_engine.inhibitions:
            self.memory.record_inhibition(inh.to_dict())

        self.memory.write_index()
        self._last = {
            "tick": tick,
            "selected_action_count": len(self.actions),
            "reaction_count": len(self.reactions),
            "consequence_count": len(self.consequences),
            "inhibition_count": len(self.inhibition_engine.inhibitions),
            "policy_update_count": len(self.policy_engine.updates),
        }
        return self._last

    def _reaction(self, kind: str, action: Any, *, valence: str):
        from .reaction import SensoriumReaction

        r = SensoriumReaction(kind=kind, action_ref=action.action_id,
                              valence=valence)
        self.reactions.append(r)
        self.memory.record_reaction(r.to_dict())
        self._milestone(ActionReactionMilestone.FIRST_REACTION)
        return r

    def _consequence(self, action: Any, reaction: Any, before: Dict[str, Any],
                     after: Dict[str, Any], tick: int) -> None:
        ctype = consequence_type_for_reaction(reaction.kind)
        trace = ConsequenceTrace(
            consequence_type=ctype, action_refs=[action.action_id],
            reaction_refs=[reaction.reaction_id],
            before_state_summary=dict(before), after_state_summary=dict(after),
            window=ConsequenceWindow(start_tick=tick,
                                     end_tick=tick + self.effect_window_ticks),
            evidence_refs=[reaction.kind],
            uncertainty=round(1.0 - reaction.magnitude, 4))
        self.consequences.append(trace)
        self.memory.record_consequence(trace.to_dict())
        self._milestone(ActionReactionMilestone.FIRST_CONSEQUENCE)

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
        for r in self.reactions:
            if r.kind in (ReactionKind.NO_EFFECT, ReactionKind.PREDICTION_FAILED,
                          ReactionKind.BLOCKED_BY_SAFETY):
                recs.append(f"replay_reaction:{r.reaction_id}:{r.kind}")
            if len(recs) >= 6:
                break
        return recs

    def hypothesis_seeds(self) -> List[Any]:
        """Action-effect hypotheses (incl. failed/no-effect)."""
        from ..hypothesis.sources import HypothesisSeed

        seeds: List[HypothesisSeed] = []
        for kind, model in self.effect_engine.models.items():
            if model.observations >= 2:
                seeds.append(HypothesisSeed(
                    source="action_reaction", hypothesis_type="relation",
                    target_ref=kind,
                    observation=f"{kind} -> {model.dominant_reaction} "
                                f"(success {model.success_rate})",
                    intensity=model.confidence,
                    evidence_refs=[f"effect:{kind}"]))
        return seeds

    def logos_tensions(self) -> List[Any]:
        """Action-reaction tensions expressed as LOGOS tensions (valid types)."""
        from ..logos_complexity.tension import (
            LogosTension,
            TensionPolarity,
            TensionType,
        )

        tensions: List[LogosTension] = []
        if any(r.kind == ReactionKind.PREDICTION_FAILED for r in self.reactions):
            tensions.append(LogosTension(
                tension_type=TensionType.PREDICTION_FAILURE,
                polarity_a="action_success", polarity_b="action_failure",
                source_modules=["action_reaction"],
                metadata={"action_reaction_tension":
                          "action_success_vs_failure"}))
        if self.habit_engine.strengthened():
            tensions.append(LogosTension(
                tension_type=TensionType.HABIT_NOVELTY,
                polarity_a=TensionPolarity.HABIT,
                polarity_b=TensionPolarity.NOVELTY,
                source_modules=["action_reaction"],
                metadata={"action_reaction_tension": "habit_vs_novelty"}))
        if self.inhibition_engine.inhibitions:
            tensions.append(LogosTension(
                tension_type=TensionType.ACTION_INHIBITION,
                polarity_a=TensionPolarity.ACTION,
                polarity_b=TensionPolarity.INHIBITION,
                source_modules=["action_reaction"],
                metadata={"action_reaction_tension": "inhibition_vs_desire"}))
        if any(r.kind == ReactionKind.NO_EFFECT for r in self.reactions):
            tensions.append(LogosTension(
                tension_type=TensionType.GROWTH_STAGNATION,
                polarity_a="action_pressure", polarity_b="no_action_result",
                source_modules=["action_reaction"],
                metadata={"action_reaction_tension": "no_action_vs_pressure"}))
        return tensions

    def metabolism_signals(self) -> Dict[str, Any]:
        constructive = sum(1 for r in self.reactions
                           if r.valence in _CONSTRUCTIVE)
        return {
            "overload_reduced": any(
                r.kind == ReactionKind.OVERLOAD_REDUCED for r in self.reactions),
            "constructive_reaction_count": constructive,
            "no_op_count": self.memory.index.no_op_count,
        }

    def action_reaction_status(self) -> Dict[str, Any]:
        rx = self.reactions
        n = max(1, len(rx))
        constructive = sum(1 for r in rx if r.valence in _CONSTRUCTIVE)
        disruptive = sum(1 for r in rx
                         if r.valence in (ReactionValence.DISRUPTIVE,
                                          ReactionValence.DESTABILIZING))
        no_effect = sum(1 for r in rx if r.kind == ReactionKind.NO_EFFECT)
        blocked = sum(1 for a in self.actions
                      if a.status == ActionExecutionStatus.BLOCKED) \
            + len(self.memory.index.blocked_action_ids)
        return {
            "action_reaction_enabled": True,
            "selected_action_count": len(self.actions),
            "internal_action_count": sum(
                1 for a in self.actions
                if a.scope in ActionScope.SAFE and not a.is_no_op),
            "blocked_action_count": len(self.memory.index.blocked_action_ids),
            "no_op_count": self.memory.index.no_op_count,
            "reaction_count": len(rx),
            "constructive_reaction_ratio": round(constructive / n, 4),
            "disruptive_reaction_ratio": round(disruptive / n, 4),
            "no_effect_action_count": no_effect,
            "consequence_trace_count": len(self.consequences),
            "learned_effect_count": self.effect_engine.learned_count(),
            "habit_candidate_count": len(self.habit_engine.candidates()),
            "strengthened_habit_count": len(self.habit_engine.strengthened()),
            "weakened_habit_count": len(self.habit_engine.weakened()),
            "inhibition_count": len(self.inhibition_engine.inhibitions),
            "action_policy_update_count": len(self.policy_engine.updates),
            "latest_action_reaction_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "ACTION_REACTION_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.action_reaction_status()

    def write_artifacts(self) -> Dict[str, Any]:
        return ActionReactionReportBuilder(self).write()
