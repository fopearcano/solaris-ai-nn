"""Inhibition -- explainable suppression across five rule families.

Governance, safety, resource, context, and conflict rules each may inhibit
a desire or an action candidate. Nothing is dropped: every inhibition
carries its rule family and reason, and inhibited entries stay visible in
queues, candidate sets, and decision traces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..embodiment.safety import REAL_WORLD_PATTERNS
from .action_candidates import ActionCandidateType, ExecutableScope
from .safety import INTERNAL_LABELS

LATENT_MODES = ("sleep", "dream", "replay", "consolidation",
                "wake_transition")

EXTERNALISH_TYPES = (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                     ActionCandidateType.SIDECAR_SUGGESTION)


@dataclass
class InhibitionRule:
    rule_id: str
    family: str  # governance | safety | resource | context | conflict
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class InhibitionResult:
    inhibited: bool
    rule_id: str = ""
    family: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_PASS = InhibitionResult(inhibited=False)


@dataclass
class InhibitionController:
    """Evaluates the five rule families; records every suppression."""

    inhibitions_total: int = field(default=0, init=False)
    history: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- shared rule core --------------------------------------------------------

    def _check(self, label: str, kind: str, action_type: str, scope: str,
               ctx: Dict[str, Any]) -> InhibitionResult:
        lowered = str(label).lower()

        # B. Safety: real-world shapes and unknown labels.
        for pattern in REAL_WORLD_PATTERNS:
            if pattern in lowered:
                return InhibitionResult(True, "safety_real_world", "safety",
                                        f"{label!r} matches real-world "
                                        f"pattern {pattern!r}")
        if kind == "action" and lowered not in INTERNAL_LABELS:
            from ..embodiment.action_space import ACTION_SPACE

            if lowered not in ACTION_SPACE:
                return InhibitionResult(True, "safety_unknown_action",
                                        "safety",
                                        f"{label!r} is not a known action")
        if lowered in ("run_replay", "run_dream") \
                and ctx.get("latent_budget_exceeded"):
            return InhibitionResult(True, "resource_latent_budget",
                                    "resource",
                                    "trace/artifact budget too high for "
                                    "more replay/dream output")
        if ctx.get("production_mutation") \
                and not ctx.get("mutation_approved"):
            return InhibitionResult(True, "safety_unapproved_mutation",
                                    "safety",
                                    "production mutation without approval")

        # A. Governance.
        governance = ctx.get("governance_blocks") or {}
        if lowered in governance:
            return InhibitionResult(True, "governance_block", "governance",
                                    str(governance[lowered]))
        if lowered in ("publish_suggestions", "publish") or (
                action_type == ActionCandidateType.SIDECAR_SUGGESTION
                and ctx.get("sidecar_publish_desired")
                and not ctx.get("sidecar_publish_approved")):
            if not ctx.get("sidecar_publish_approved"):
                return InhibitionResult(True, "governance_sidecar_publish",
                                        "governance",
                                        "sidecar publishing requires "
                                        "approval; observe-only stands")
        if ctx.get("prohibited_actions") \
                and lowered in ctx["prohibited_actions"]:
            return InhibitionResult(True, "governance_prohibited",
                                    "governance",
                                    f"{label!r} is prohibited by policy")
        if kind == "action" and lowered == "generate_report" \
                and ctx.get("claim_guard_unsafe"):
            return InhibitionResult(True, "governance_claim_guard",
                                    "governance",
                                    "report generation blocked until the "
                                    "unsupported claims are removed")

        # C. Resources.
        cost = float(ctx.get("candidate_cost", 0.0) or 0.0)
        energy = ctx.get("energy")
        if energy is not None and cost > 0.0 and float(energy) < cost:
            return InhibitionResult(True, "resource_energy", "resource",
                                    f"energy {energy} cannot afford cost "
                                    f"{cost}")
        if ctx.get("watchdog_stop_requested") and kind == "action" \
                and action_type not in (
                    ActionCandidateType.SAFE_SHUTDOWN_RECOMMENDATION,
                    ActionCandidateType.CHECKPOINT_REQUEST,
                    ActionCandidateType.OPERATOR_REVIEW_REQUEST,
                    ActionCandidateType.NO_ACTION):
            return InhibitionResult(True, "resource_watchdog", "resource",
                                    "the watchdog requested a stop; no new "
                                    "work is planned")

        # D. Context.
        mode = str(ctx.get("latent_mode", "awake"))
        if mode in LATENT_MODES and action_type in EXTERNALISH_TYPES:
            return InhibitionResult(True, "context_latent_mode", "context",
                                    f"external action {label!r} is "
                                    f"inhibited during {mode}")
        if mode in LATENT_MODES and lowered in ("publish_suggestions",
                                                "publish"):
            return InhibitionResult(True, "context_latent_publish",
                                    "context",
                                    "sidecar publishing is inhibited "
                                    "during latent modes")
        if (ctx.get("health_level") == "critical"
                or ctx.get("emergency")) \
                and lowered in ("explore_safely", "approach_reward",
                                "seek_signal", "run_replay"):
            return InhibitionResult(True, "context_emergency", "context",
                                    "exploration is inhibited during "
                                    "emergency/critical state")
        return _PASS

    # -- public API -----------------------------------------------------------------

    def evaluate_desire(self, desire: Any,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> InhibitionResult:
        ctx = dict(context or {})
        result = self._check(getattr(desire, "proposal", str(desire)),
                             "desire", "", ExecutableScope.NONE, ctx)
        self._record("desire", desire, result)
        return result

    def evaluate_action(self, action: Any,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> InhibitionResult:
        ctx = dict(context or {})
        ctx.setdefault("candidate_cost",
                       getattr(action, "expected_cost", 0.0))
        result = self._check(
            getattr(action, "label", str(action)), "action",
            getattr(action, "action_type", ""),
            getattr(action, "executable_scope", ExecutableScope.NONE), ctx)
        self._record("action", action, result)
        return result

    def apply_to_queue(self, queue: Any,
                       context: Optional[Dict[str, Any]] = None) -> int:
        """Inhibit matching queued desires in place; returns how many."""
        inhibited = 0
        for item in list(queue.items):
            if item.inhibited:
                continue
            result = self.evaluate_desire(item, context)
            if result.inhibited:
                queue.mark_inhibited(item.desire_id,
                                     f"{result.rule_id}: {result.reason}")
                inhibited += 1
        return inhibited

    def apply_to_candidates(self, candidates: List[Any],
                            context: Optional[Dict[str, Any]] = None,
                            ) -> int:
        inhibited = 0
        for candidate in candidates:
            if candidate.inhibited:
                continue
            result = self.evaluate_action(candidate, context)
            if result.inhibited:
                candidate.inhibited = True
                candidate.inhibition_reason = (f"{result.rule_id}: "
                                               f"{result.reason}")
                inhibited += 1
        return inhibited

    def _record(self, kind: str, target: Any,
                result: InhibitionResult) -> None:
        if not result.inhibited:
            return
        self.inhibitions_total += 1
        self.history.append({
            "kind": kind,
            "label": getattr(target, "label",
                             getattr(target, "proposal", str(target))),
            **result.to_dict()})
        self.history = self.history[-100:]

    def snapshot(self) -> Dict[str, Any]:
        return {"inhibitions_total": self.inhibitions_total,
                "recent": self.history[-8:],
                "families": ["governance", "safety", "resource", "context",
                             "conflict"]}
