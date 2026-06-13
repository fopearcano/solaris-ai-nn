"""Active sensing -- propose, gate, and (safely) execute sampling.

The :class:`ActiveSensingController` is the orchestrator. It assembles a
normalized context from whatever components are attached (Mysterium, world
model, proto-language, homeostasis, ecology, executive, ego boundaries),
estimates salience/uncertainty/curiosity/stagnation, asks the policy for a
decision, routes the chosen action through the safety validator, governance,
and ego boundary classification, and only then *applies* it -- and only if
its scope is simulation / internal / read-only / sidecar-observe. Results are
recorded in exploration memory. Nothing here acts in the real world, commits
a sidecar action, calls the network, or bypasses the executive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .attention_control import ActiveAttentionController
from .curiosity import CuriosityEstimator
from .exploration_memory import (
    ExplorationMemory,
    ExplorationOutcome,
    ExplorationRecord,
)
from .information_gain import InformationGainEstimator
from .safety import ActivePerceptionSafetyValidator
from .salience import SalienceEstimator
from .sampling_actions import (
    SamplingAction,
    SamplingActionResult,
    SamplingActionType,
    SamplingScope,
)
from .sampling_policy import SamplingDecision, SamplingPolicy, SamplingPolicyMode
from .stagnation import StagnationDetector
from .uncertainty import UncertaintyEstimator


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


# Sampling scope -> the ego boundary it crosses (for attribution).
def _boundary_for_scope(scope: str) -> str:
    from ..ego.boundaries import BoundaryType

    return {
        SamplingScope.SIMULATION_ONLY: BoundaryType.SIMULATION,
        SamplingScope.INTERNAL_ONLY: BoundaryType.LATENT_OFFLINE,
        SamplingScope.READ_ONLY_STREAM: BoundaryType.PILOT_INPUT,
        SamplingScope.SIDECAR_OBSERVE_ONLY: BoundaryType.SIDECAR,
    }.get(scope, BoundaryType.ACTION_AUTHORITY)


# Ego classification labels for a sampling action's scope.
SCOPE_CLASSIFICATION = {
    SamplingScope.SIMULATION_ONLY: "simulated_sampling",
    SamplingScope.INTERNAL_ONLY: "internal_sampling",
    SamplingScope.READ_ONLY_STREAM: "read_only_sampling",
    SamplingScope.SIDECAR_OBSERVE_ONLY: "sidecar_observation",
    SamplingScope.FORBIDDEN: "forbidden",
}


@dataclass
class ActiveSensingController:
    """Proposes and safely executes self-directed sampling."""

    policy: SamplingPolicy = field(default_factory=SamplingPolicy)
    safety: ActivePerceptionSafetyValidator = field(
        default_factory=ActivePerceptionSafetyValidator)
    memory: ExplorationMemory = field(default_factory=ExplorationMemory)
    attention: ActiveAttentionController = field(
        default_factory=ActiveAttentionController)
    # Optional component references (all duck-typed; any may be None).
    nursery: Any = None
    world_model: Any = None
    protolanguage: Any = None
    homeostasis: Any = None
    executive: Any = None
    ego_boundaries: Any = None
    governance: Any = None
    latent: Any = None
    # Whether curiosity-driven mode is permitted (governance config).
    curiosity_enabled: bool = False
    enabled: bool = True

    blocked_count: int = field(default=0, init=False)
    last_decision: Optional[SamplingDecision] = field(default=None, init=False)
    last_result: Optional[SamplingActionResult] = field(default=None,
                                                        init=False)
    _last_action_type: Optional[str] = field(default=None, init=False)
    _repeat_count: int = field(default=0, init=False)

    # -- context assembly ---------------------------------------------------------

    def build_context(self, extra: Optional[Dict[str, Any]] = None,
                      ) -> Dict[str, Any]:
        """Assemble a normalized context dict from attached components."""
        ctx: Dict[str, Any] = dict(extra or {})
        if self.world_model is not None and "world_model" not in ctx:
            try:
                ctx["world_model"] = self.world_model.world_model_summary()
            except Exception:  # observation is best-effort
                pass
        if self.protolanguage is not None and "proto_language" not in ctx:
            try:
                ctx["proto_language"] = self.protolanguage.summary()
            except Exception:
                pass
        if self.nursery is not None and "ecology" not in ctx:
            try:
                ctx["ecology"] = self.nursery.summary()
                ctx.setdefault("novelty_rate",
                               _num(ctx["ecology"], "novelty_rate"))
                ctx.setdefault("absence_rate",
                               _num(ctx["ecology"], "absence_rate"))
            except Exception:
                pass
        if self.homeostasis is not None and "homeostasis" not in ctx:
            try:
                ctx["homeostasis"] = self.homeostasis.summary()
            except Exception:
                pass
        return ctx

    # -- proposal / selection -----------------------------------------------------

    def _precompute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ctx = dict(context or {})
        ctx["salience_map"] = self.policy.salience.estimate(ctx)
        ctx["uncertainty_state"] = self.policy.uncertainty.estimate(ctx)
        ctx["curiosity_state"] = self.policy.curiosity.estimate(ctx)
        ctx["stagnation_status"] = self.policy.stagnation.detect(ctx).status
        # Governance: curiosity-driven mode requires explicit config.
        if self.policy.mode == SamplingPolicyMode.CURIOSITY_DRIVEN \
                and not self.curiosity_enabled:
            self.policy.mode = SamplingPolicyMode.BALANCED
        self.attention.select_focus(ctx)
        return ctx

    def propose(self, context: Dict[str, Any]) -> List[SamplingAction]:
        if not self.enabled:
            return []
        ctx = self._precompute(context)
        actions = self.policy.select_actions(ctx)
        report = self.safety.validate_batch(actions)
        if not report.safe:
            from .safety import MAX_ACTIONS_PER_STEP

            actions = actions[:MAX_ACTIONS_PER_STEP]
        return actions

    def select(self, context: Dict[str, Any]) -> SamplingDecision:
        ctx = self._precompute(context)
        decision = self.policy.select_best_action(ctx)
        self.last_decision = decision
        return decision

    # -- execution ----------------------------------------------------------------

    def execute_if_allowed(self, decision: SamplingDecision,
                          context: Dict[str, Any]) -> SamplingActionResult:
        ctx = dict(context or {})
        action = decision.action
        result = SamplingActionResult(
            action_id=action.action_id, action_type=action.action_type,
            scope=action.scope, cost=float(action.expected_cost))

        # No-op action: always allowed, nothing executed.
        if action.action_type == SamplingActionType.NO_SAMPLING_ACTION:
            result.outcome = ExplorationOutcome.NEUTRAL
            result.detail = action.metadata.get("reason", "no sampling")
            self.last_result = result
            return result

        # Loop guard.
        if action.action_type == self._last_action_type:
            self._repeat_count += 1
        else:
            self._repeat_count = 0
        self._last_action_type = action.action_type
        loop_report = self.safety.validate_loop(self._repeat_count)

        # Safety validation.
        safety_report = self.safety.validate_action(action, ctx)
        if not safety_report.safe or not loop_report.safe:
            return self._blocked(
                action, result,
                "; ".join(safety_report.violations + loop_report.violations))

        # Governance: actions never match real-world patterns, but route them.
        if self.governance is not None:
            gov = self.governance.evaluate_action(action.action_type, ctx)
            action.governance_status = "ok" if gov.allowed else "denied"
            if not gov.allowed:
                return self._blocked(action, result,
                                    "; ".join(gov.reasons) or "governance denied")

        # Ego boundary classification (record the crossing; block on violation).
        classification = self._classify_and_record(action, ctx)
        result.metadata["classification"] = classification
        if classification == "forbidden":
            return self._blocked(action, result,
                                "ego boundary forbids this sampling scope")

        # Scope must be runnable.
        if action.scope not in SamplingScope.RUNNABLE:
            return self._blocked(action, result,
                                f"scope {action.scope} is not runnable")

        # Apply within the permitted scope.
        action.safety_status = "ok"
        result.safety_status = "ok"
        result.executed = True
        result.detail = self._apply(action, ctx)
        result.outcome = ExplorationOutcome.UNKNOWN  # scored later
        self.last_result = result
        return result

    def _blocked(self, action: SamplingAction, result: SamplingActionResult,
                reason: str) -> SamplingActionResult:
        result.blocked = True
        result.executed = False
        result.blocked_reason = reason
        result.outcome = ExplorationOutcome.BLOCKED
        result.safety_status = "blocked"
        action.safety_status = "blocked"
        self.blocked_count += 1
        self.last_result = result
        return result

    def _classify_and_record(self, action: SamplingAction,
                            context: Dict[str, Any]) -> str:
        classification = SCOPE_CLASSIFICATION.get(action.scope, "forbidden")
        if self.ego_boundaries is not None and classification != "forbidden":
            try:
                from ..ego.boundaries import BoundaryType

                boundary = _boundary_for_scope(action.scope)
                if context.get("treat_stream_as_command") \
                        and boundary == BoundaryType.PILOT_INPUT:
                    self.ego_boundaries.record_violation(
                        boundary, "sampling treated stream text as command")
                    return "forbidden"
                self.ego_boundaries.record_crossing(
                    boundary,
                    f"active sampling: {action.action_type}",
                    direction="inbound",
                    evidence=[f"action:{action.action_id}"])
            except Exception:  # boundary bookkeeping is best-effort
                pass
        return classification

    def _apply(self, action: SamplingAction, context: Dict[str, Any]) -> str:
        """Apply the action within its scope; simulation/internal/read-only."""
        atype = action.action_type
        # Simulated actions: route to the nursery's sampling hooks if present.
        if atype in SamplingActionType.SIMULATED and self.nursery is not None:
            hook = getattr(self.nursery, "sample", None)
            if callable(hook):
                try:
                    detail = hook(atype, action.target_ref)
                    return f"nursery sampled: {detail}"
                except Exception as exc:
                    return f"nursery sampling no-op ({exc})"
        # Internal/offline actions: route to latent if present (replay only).
        if atype == SamplingActionType.REPLAY_UNCERTAIN_TRACE \
                and self.latent is not None:
            return "internal replay (offline, labelled simulated)"
        if atype == SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING:
            return "internal consolidation requested (offline)"
        if atype == SamplingActionType.INSPECT_WORLD_MODEL_NODE \
                and self.world_model is not None:
            return f"inspected world-model node {action.target_ref}"
        if atype == SamplingActionType.INSPECT_PROTO_SYMBOL \
                and self.protolanguage is not None:
            return f"inspected proto-symbol {action.target_ref}"
        return f"{atype} applied (scope {action.scope})"

    # -- result observation -------------------------------------------------------

    def observe_result(self, result: SamplingActionResult,
                       before_context: Dict[str, Any],
                       after_context: Dict[str, Any]) -> ExplorationRecord:
        before, after = dict(before_context or {}), dict(after_context or {})
        action = (self.last_decision.action
                  if self.last_decision else None)
        observed = 0.0
        if action is not None and not result.blocked:
            observed = self.policy.information_gain.score_observed_result(
                action, result, before, after)
            result.observed_information_gain = observed
            result.outcome = self._classify_outcome(observed, result)
        wm_b = (before.get("world_model") or {})
        wm_a = (after.get("world_model") or {})
        proto_b = (before.get("proto_language") or {})
        proto_a = (after.get("proto_language") or {})
        record = ExplorationRecord(
            action_id=result.action_id, action_type=result.action_type,
            scope=result.scope,
            source_pressure=(action.source_pressure if action else ""),
            expected_information_gain=(
                float(action.expected_information_gain) if action else 0.0),
            observed_information_gain=observed,
            cost=result.cost,
            mysterium_before=before.get("mysterium_pressure"),
            mysterium_after=after.get("mysterium_pressure"),
            prediction_accuracy_before=wm_b.get("prediction_accuracy"),
            prediction_accuracy_after=wm_a.get("prediction_accuracy"),
            world_model_confidence_before=wm_b.get("prediction_accuracy"),
            world_model_confidence_after=wm_a.get("prediction_accuracy"),
            proto_symbol_ambiguity_before=proto_b.get(
                "ambiguous_symbol_count"),
            proto_symbol_ambiguity_after=proto_a.get(
                "ambiguous_symbol_count"),
            safety_status=result.safety_status,
            outcome=result.outcome,
            step=int(after.get("step", before.get("step", 0)) or 0))
        self.memory.record(record)
        self.policy.update_from_result(result)
        return record

    def _classify_outcome(self, observed: float,
                         result: SamplingActionResult) -> str:
        if result.blocked:
            return ExplorationOutcome.BLOCKED
        if observed > 0.02:
            return ExplorationOutcome.USEFUL
        if observed < -0.02:
            return ExplorationOutcome.HARMFUL
        return ExplorationOutcome.NEUTRAL

    # -- view ---------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "curiosity_enabled": self.curiosity_enabled,
            "policy": self.policy.snapshot(),
            "attention": self.attention.snapshot(),
            "salience": self.policy.salience.snapshot(),
            "uncertainty": self.policy.uncertainty.snapshot(),
            "curiosity": self.policy.curiosity.snapshot(),
            "stagnation": self.policy.stagnation.snapshot(),
            "information_gain": self.policy.information_gain.snapshot(),
            "exploration_memory": self.memory.snapshot(),
            "safety": self.safety.snapshot(),
            "blocked_count": self.blocked_count,
            "last_result": (self.last_result.to_dict()
                            if self.last_result else None),
        }
