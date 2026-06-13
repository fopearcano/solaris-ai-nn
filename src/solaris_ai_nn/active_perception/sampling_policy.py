"""Sampling policy -- which safe sampling actions to propose, and why.

The policy maps the current salience / uncertainty / curiosity / stagnation
picture onto a small set of candidate :class:`SamplingAction`s according to a
mode (passive, balanced, curiosity_driven, conservative, recovery,
stabilization, emergency), scores them by expected information gain, and
returns a :class:`SamplingDecision`. Governance and safety always dominate:
when no safe sampling exists, the policy chooses ``no_sampling_action``. The
policy is deterministic given its seed/config and the context.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .curiosity import CuriosityEstimator, CuriosityState
from .information_gain import InformationGainEstimator
from .salience import SalienceEstimator, SalienceMap
from .sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingPressure,
    SamplingScope,
    default_scope,
    no_sampling_action,
)
from .stagnation import StagnationDetector, StagnationStatus
from .uncertainty import (
    UncertaintyEstimator,
    UncertaintySource,
    UncertaintyState,
)


class SamplingPolicyMode:
    PASSIVE = "passive"
    BALANCED = "balanced"
    CURIOSITY_DRIVEN = "curiosity_driven"
    CONSERVATIVE = "conservative"
    RECOVERY = "recovery"
    STABILIZATION = "stabilization"
    EMERGENCY = "emergency"

    ALL = (PASSIVE, BALANCED, CURIOSITY_DRIVEN, CONSERVATIVE, RECOVERY,
           STABILIZATION, EMERGENCY)


# Uncertainty source -> (sampling action, motivating pressure tag).
_SOURCE_TO_ACTION = {
    UncertaintySource.WORLD_MODEL_CONFIDENCE: (
        SamplingActionType.INSPECT_WORLD_MODEL_NODE,
        SamplingPressure.WORLD_MODEL_UNCERTAINTY),
    UncertaintySource.WEAK_CAUSAL_CANDIDATE: (
        SamplingActionType.SAMPLE_UNKNOWN_REGION,
        SamplingPressure.WORLD_MODEL_UNCERTAINTY),
    UncertaintySource.PROTO_SYMBOL_AMBIGUITY: (
        SamplingActionType.INSPECT_PROTO_SYMBOL,
        SamplingPressure.PROTO_SYMBOL_AMBIGUITY),
    UncertaintySource.MYSTERIUM: (
        SamplingActionType.REPLAY_UNCERTAIN_TRACE,
        SamplingPressure.MYSTERIUM),
    UncertaintySource.ANTICIPATION_MISS: (
        SamplingActionType.SAMPLE_KNOWN_PATTERN,
        SamplingPressure.PREDICTION_ERROR),
    UncertaintySource.COUNTERFACTUAL_DIVERGENCE: (
        SamplingActionType.REPLAY_UNCERTAIN_TRACE,
        SamplingPressure.MYSTERIUM),
    UncertaintySource.REPEATED_ANOMALY: (
        SamplingActionType.FOCUS_SIGNAL_SOURCE,
        SamplingPressure.PREDICTION_ERROR),
    UncertaintySource.EXECUTIVE_CONFLICT: (
        SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING,
        SamplingPressure.HOMEOSTASIS),
    UncertaintySource.EGO_ATTRIBUTION: (
        SamplingActionType.INSPECT_WORLD_MODEL_NODE,
        SamplingPressure.WORLD_MODEL_UNCERTAINTY),
    UncertaintySource.MEMORY_COMPRESSION_LOSS: (
        SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING,
        SamplingPressure.HOMEOSTASIS),
}


@dataclass
class SamplingDecision:
    """The selected action plus the alternatives and the reasoning."""

    action: SamplingAction
    alternatives: List[SamplingAction] = field(default_factory=list)
    mode: str = SamplingPolicyMode.BALANCED
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.to_dict(),
            "alternatives": [a.to_dict() for a in self.alternatives],
            "mode": self.mode,
            "reason": self.reason,
        }


@dataclass
class SamplingPolicy:
    """Selects safe sampling actions by mode; governance/safety dominate."""

    mode: str = SamplingPolicyMode.BALANCED
    seed: int = 7
    max_actions: int = 4
    salience: SalienceEstimator = field(default_factory=SalienceEstimator)
    uncertainty: UncertaintyEstimator = field(
        default_factory=UncertaintyEstimator)
    curiosity: CuriosityEstimator = field(default_factory=CuriosityEstimator)
    information_gain: InformationGainEstimator = field(
        default_factory=InformationGainEstimator)
    stagnation: StagnationDetector = field(default_factory=StagnationDetector)
    decisions_made: int = field(default=0, init=False)
    last_decision: Optional[SamplingDecision] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.mode not in SamplingPolicyMode.ALL:
            raise ValueError(f"unknown sampling policy mode {self.mode!r}")
        self._rng = random.Random(self.seed)

    # -- effective mode -----------------------------------------------------------

    def _effective_mode(self, context: Dict[str, Any],
                        curiosity: CuriosityState) -> str:
        """Safety/overload can force a stricter mode than configured."""
        if context.get("emergency") or context.get(
                "emergency_stop_requested") \
                or context.get("health_level") == "critical":
            return SamplingPolicyMode.EMERGENCY
        if context.get("safety_incident") or context.get(
                "boundary_violation"):
            return SamplingPolicyMode.CONSERVATIVE
        # Overload -> recovery (low energy / high fatigue / runaway anomaly).
        energy = context.get("energy")
        overloaded = ((energy is not None and float(energy) < 0.25)
                      or float(context.get("fatigue", 0.0) or 0.0) > 0.7
                      or float((context.get("ecology") or {}).get(
                          "anomaly_rate", 0.0) or 0.0) > 0.4)
        if overloaded and self.mode != SamplingPolicyMode.PASSIVE:
            return SamplingPolicyMode.RECOVERY
        return self.mode

    # -- candidate generation -----------------------------------------------------

    def _candidates_for_mode(self, mode: str, context: Dict[str, Any],
                            uncertainty: UncertaintyState,
                            curiosity: CuriosityState,
                            stagnation_status: str,
                            ) -> List[SamplingAction]:
        if mode in (SamplingPolicyMode.EMERGENCY,):
            return []  # only no_sampling_action; safe shutdown is ops' job
        if mode == SamplingPolicyMode.PASSIVE:
            return []  # passive: no active sampling except safety/ops

        actions: List[SamplingAction] = []

        def add(action_type: str, target: Optional[str], pressure: str,
                cost: float = 0.05, risk: float = 0.05) -> None:
            actions.append(SamplingAction(
                action_type=action_type, scope=default_scope(action_type),
                target_ref=target, source_pressure=pressure,
                expected_cost=cost, expected_risk=risk,
                confidence=0.6))

        if mode == SamplingPolicyMode.RECOVERY:
            add(SamplingActionType.REST, None, SamplingPressure.HOMEOSTASIS,
                cost=0.0)
            add(SamplingActionType.WAIT, None, SamplingPressure.ECOLOGY_CYCLE,
                cost=0.0)
            add(SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING, "memory",
                SamplingPressure.HOMEOSTASIS, cost=0.05)
            if float((context.get("ecology") or {}).get(
                    "anomaly_rate", 0.0) or 0.0) > 0.3:
                add(SamplingActionType.SEEK_ABSENCE, "low_stimulus_region",
                    SamplingPressure.ECOLOGY_CYCLE)
            return actions

        # Uncertainty-driven candidates (balanced / curiosity / conservative /
        # stabilization all start from uncertain targets).
        for target in uncertainty.top_targets(self.max_actions):
            action_type, pressure = _SOURCE_TO_ACTION.get(
                target.source,
                (SamplingActionType.LOOK, SamplingPressure.PREDICTION_ERROR))
            # Conservative/stabilization never sample unknown regions/novelty.
            if mode in (SamplingPolicyMode.CONSERVATIVE,
                        SamplingPolicyMode.STABILIZATION) \
                    and action_type in (
                        SamplingActionType.SAMPLE_UNKNOWN_REGION,):
                action_type = SamplingActionType.SAMPLE_KNOWN_PATTERN
            add(action_type, target.target_ref, pressure,
                risk=round(0.05 + 0.1 * target.uncertainty, 4))

        if mode == SamplingPolicyMode.CURIOSITY_DRIVEN \
                and not curiosity.suppressed_by_safety:
            add(SamplingActionType.SEEK_NOVELTY, "novel_region",
                SamplingPressure.MYSTERIUM, risk=0.15)
            add(SamplingActionType.SAMPLE_UNKNOWN_REGION, "unknown_region",
                SamplingPressure.WORLD_MODEL_UNCERTAINTY, risk=0.15)
        if mode == SamplingPolicyMode.CONSERVATIVE:
            add(SamplingActionType.SAMPLE_KNOWN_PATTERN, "known_pattern",
                SamplingPressure.PREDICTION_ERROR)
            add(SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING, "memory",
                SamplingPressure.HOMEOSTASIS)
        if mode == SamplingPolicyMode.STABILIZATION:
            add(SamplingActionType.SAMPLE_KNOWN_PATTERN, "stable_pattern",
                SamplingPressure.PREDICTION_ERROR)
        if mode == SamplingPolicyMode.BALANCED \
                and stagnation_status in (StagnationStatus.STAGNATING,
                                          StagnationStatus.INERT) \
                and not curiosity.suppressed_by_safety:
            add(SamplingActionType.SEEK_NOVELTY, "novel_region",
                SamplingPressure.DEVELOPMENTAL_STAGNATION, risk=0.12)
        return actions

    # -- selection ----------------------------------------------------------------

    def select_actions(self, context: Dict[str, Any]) -> List[SamplingAction]:
        ctx = dict(context or {})
        # Reuse precomputed estimates when the controller supplies them.
        smap: SalienceMap = ctx.get("salience_map") or self.salience.estimate(
            ctx)
        ustate: UncertaintyState = ctx.get(
            "uncertainty_state") or self.uncertainty.estimate(ctx)
        cstate: CuriosityState = ctx.get(
            "curiosity_state") or self.curiosity.estimate(ctx)
        stagnation_status = ctx.get("stagnation_status")
        if stagnation_status is None:
            stagnation_status = self.stagnation.detect(ctx).status
        ctx.setdefault("salience_map", smap)

        mode = self._effective_mode(ctx, cstate)
        candidates = self._candidates_for_mode(
            mode, ctx, ustate, cstate, stagnation_status)
        # Score by expected information gain.
        scored = self.information_gain.compare_actions(candidates, ctx)
        gains = {e.action_id: e for e in scored}
        for action in candidates:
            est = gains.get(action.action_id)
            if est is not None:
                action.expected_information_gain = est.expected_gain
                action.confidence = est.confidence
        candidates.sort(key=lambda a: a.expected_information_gain,
                        reverse=True)
        return candidates[:self.max_actions]

    def select_best_action(self, context: Dict[str, Any]) -> SamplingDecision:
        ctx = dict(context or {})
        cstate = ctx.get("curiosity_state") or self.curiosity.estimate(ctx)
        mode = self._effective_mode(ctx, cstate)
        actions = self.select_actions(ctx)
        if not actions:
            reason = {
                SamplingPolicyMode.EMERGENCY:
                    "emergency mode: no sampling except safe shutdown/report",
                SamplingPolicyMode.PASSIVE:
                    "passive mode: no active sampling",
            }.get(mode, "no safe sampling action available")
            decision = SamplingDecision(
                action=no_sampling_action(reason), alternatives=[],
                mode=mode, reason=reason)
        else:
            best = actions[0]
            decision = SamplingDecision(
                action=best, alternatives=actions[1:], mode=mode,
                reason=f"highest expected information gain "
                       f"({best.expected_information_gain}) for "
                       f"{best.action_type} under {mode} mode")
        self.decisions_made += 1
        self.last_decision = decision
        return decision

    def update_from_result(self, result: Any) -> None:
        """Record outcome feedback (kept simple; memory holds the detail)."""
        outcome = getattr(result, "outcome", None) or (
            result.get("outcome") if isinstance(result, dict) else None)
        self._last_outcome = outcome

    def set_mode(self, mode: str) -> None:
        if mode not in SamplingPolicyMode.ALL:
            raise ValueError(f"unknown sampling policy mode {mode!r}")
        self.mode = mode

    def snapshot(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "seed": self.seed,
            "max_actions": self.max_actions,
            "decisions_made": self.decisions_made,
            "last_decision": (self.last_decision.to_dict()
                              if self.last_decision else None),
        }
