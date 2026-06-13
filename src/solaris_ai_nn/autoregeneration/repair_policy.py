"""Repair policy -- which bounded repairs to propose, and whether to apply.

The :class:`RepairPolicy` maps degradation signals onto candidate
:class:`RepairAction`s and decides, per mode, whether each may be applied.
Source-code repair is always forbidden, governance hard rules cannot be
repaired away, the emergency stop always wins, and unsafe actions are
refused. Deterministic given the degradation state and context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .degradation import (
    DegradationSeverity,
    DegradationSignal,
    DegradationState,
    DegradationType,
)
from .repair_actions import (
    RepairAction,
    RepairActionType,
    make_repair,
    no_repair,
)


class RepairPolicyMode:
    OBSERVE_ONLY = "observe_only"
    SUGGEST_ONLY = "suggest_only"
    SAFE_AUTO_REPAIR = "safe_auto_repair"
    GOVERNED_REPAIR = "governed_repair"
    EMERGENCY_STABILIZATION = "emergency_stabilization"

    ALL = (OBSERVE_ONLY, SUGGEST_ONLY, SAFE_AUTO_REPAIR, GOVERNED_REPAIR,
           EMERGENCY_STABILIZATION)


# Degradation type -> repair action type to propose.
_REPAIR_MAP = {
    DegradationType.MEMORY_BLOAT: RepairActionType.COMPACT_MEMORY_LAYER,
    DegradationType.STATE_FILE_CORRUPTION:
        RepairActionType.QUARANTINE_CORRUPT_RECORD,
    DegradationType.CHECKPOINT_INCONSISTENCY:
        RepairActionType.RESTORE_FROM_CHECKPOINT,
    DegradationType.BROKEN_REFERENCE:
        RepairActionType.REPAIR_BROKEN_REFERENCE,
    DegradationType.TELEMETRY_OVERGROWTH:
        RepairActionType.ARCHIVE_OLD_TELEMETRY,
    DegradationType.SYMBOL_EXPLOSION: RepairActionType.MARK_SYMBOL_STALE,
    DegradationType.SYMBOL_STALENESS: RepairActionType.MARK_SYMBOL_STALE,
    DegradationType.WORLD_MODEL_CONTRADICTION:
        RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS,
    DegradationType.WORLD_MODEL_EDGE_DECAY:
        RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS,
    DegradationType.HABIT_DEAD_LOOP: RepairActionType.RETIRE_DEAD_HABIT,
    DegradationType.HABIT_RUNAWAY: RepairActionType.DECAY_RUNAWAY_HABIT,
    DegradationType.PREDICTION_DEGRADATION:
        RepairActionType.REQUEST_LATENT_REPLAY,
    DegradationType.MYSTERIUM_SATURATION:
        RepairActionType.REQUEST_LATENT_REPLAY,
    DegradationType.EXECUTIVE_LOOP:
        RepairActionType.SWITCH_TO_STABILIZATION_MODE,
    DegradationType.HOMEOSTATIC_INSTABILITY:
        RepairActionType.SWITCH_TO_STABILIZATION_MODE,
    DegradationType.DRIFT_RUNAWAY:
        RepairActionType.SWITCH_TO_STABILIZATION_MODE,
    DegradationType.DEVELOPMENTAL_STAGNATION:
        RepairActionType.REQUEST_LATENT_REPLAY,
    DegradationType.HYPOTHESIS_INCONCLUSIVE_LOOP:
        RepairActionType.REQUEST_CONSOLIDATION,
    DegradationType.UNSAFE_SAMPLING_REPETITION:
        RepairActionType.REDUCE_SAMPLING_RATE,
    DegradationType.IDENTITY_CONTINUITY_GAP:
        RepairActionType.GENERATE_OPERATOR_REVIEW_REQUEST,
    DegradationType.UNKNOWN: RepairActionType.NO_REPAIR,
}

# Repairs that emergency-stabilization is allowed to propose/apply.
_EMERGENCY_ALLOWED = frozenset({
    RepairActionType.SWITCH_TO_STABILIZATION_MODE,
    RepairActionType.REDUCE_SAMPLING_RATE,
    RepairActionType.REQUEST_CONSOLIDATION,
    RepairActionType.GENERATE_OPERATOR_REVIEW_REQUEST,
    RepairActionType.NO_REPAIR,
})

# Low-risk reversible repairs safe_auto_repair may apply without approval.
_SAFE_AUTO_ALLOWED = frozenset({
    RepairActionType.COMPACT_MEMORY_LAYER,
    RepairActionType.ARCHIVE_OLD_TELEMETRY,
    RepairActionType.REBUILD_INDEX,
    RepairActionType.REPAIR_BROKEN_REFERENCE,
    RepairActionType.QUARANTINE_CORRUPT_RECORD,
    RepairActionType.MARK_SYMBOL_STALE,
    RepairActionType.MERGE_DUPLICATE_SYMBOLS,
    RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS,
    RepairActionType.REQUEST_CONSOLIDATION,
    RepairActionType.REQUEST_LATENT_REPLAY,
    RepairActionType.REDUCE_SAMPLING_RATE,
    RepairActionType.SWITCH_TO_STABILIZATION_MODE,
    RepairActionType.GENERATE_OPERATOR_REVIEW_REQUEST,
    RepairActionType.NO_REPAIR,
})


@dataclass
class RepairDecision:
    """A proposed repair plus whether the current mode may apply it."""

    action: RepairAction
    mode: str
    apply_allowed: bool = False
    requires_governance: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action.to_dict(), "mode": self.mode,
                "apply_allowed": self.apply_allowed,
                "requires_governance": self.requires_governance,
                "reason": self.reason}


@dataclass
class RepairPolicy:
    """Proposes repairs and decides applicability by mode."""

    mode: str = RepairPolicyMode.OBSERVE_ONLY

    def __post_init__(self) -> None:
        if self.mode not in RepairPolicyMode.ALL:
            raise ValueError(f"unknown repair policy mode {self.mode!r}")

    def _effective_mode(self, context: Dict[str, Any]) -> str:
        ctx = dict(context or {})
        if ctx.get("emergency") or ctx.get("emergency_stop_requested") \
                or ctx.get("health_level") == "critical":
            return RepairPolicyMode.EMERGENCY_STABILIZATION
        return self.mode

    def _action_for(self, signal: DegradationSignal) -> RepairAction:
        action_type = _REPAIR_MAP.get(signal.type, RepairActionType.NO_REPAIR)
        target = (signal.metric_snapshot.get("target")
                  or (signal.evidence_refs[0] if signal.evidence_refs
                      else signal.type))
        action = make_repair(
            action_type, target_ref=str(target),
            reason=f"repair for {signal.type} ({signal.severity})",
            expected_benefit=f"reduce {signal.type}",
            degradation_type=signal.type, severity=signal.severity,
            signal_id=signal.signal_id)
        if signal.requires_governance:
            action.requires_governance = True
        return action

    def propose(self, state: DegradationState,
                context: Optional[Dict[str, Any]] = None,
                ) -> List[RepairDecision]:
        ctx = dict(context or {})
        mode = self._effective_mode(ctx)
        if mode == RepairPolicyMode.OBSERVE_ONLY:
            return []  # diagnostics only
        decisions: List[RepairDecision] = []
        for signal in state.ranked():
            if not signal.repairable:
                continue
            action = self._action_for(signal)
            apply_allowed, reason = self._apply_decision(action, mode, ctx)
            decisions.append(RepairDecision(
                action=action, mode=mode, apply_allowed=apply_allowed,
                requires_governance=action.requires_governance,
                reason=reason))
        if not decisions:
            decisions.append(RepairDecision(
                action=no_repair(), mode=mode, apply_allowed=False,
                reason="no repairable degradation"))
        return decisions

    def _apply_decision(self, action: RepairAction, mode: str,
                       ctx: Dict[str, Any]) -> "tuple[bool, str]":
        atype = action.action_type
        if mode == RepairPolicyMode.SUGGEST_ONLY:
            return (False, "suggest-only: proposed, not applied")
        if mode == RepairPolicyMode.EMERGENCY_STABILIZATION:
            if atype in _EMERGENCY_ALLOWED:
                return (True, "emergency stabilization: risk-reducing repair")
            return (False, "emergency stabilization: only risk-reducing "
                           "repairs are applied")
        if mode == RepairPolicyMode.GOVERNED_REPAIR:
            if action.requires_governance and not ctx.get(
                    "governance_approved"):
                return (False, "governed repair: governance approval required")
            return (True, "governed repair: approved/low-risk")
        if mode == RepairPolicyMode.SAFE_AUTO_REPAIR:
            if action.requires_governance:
                return (False, "safe-auto: this repair needs governance")
            if atype in _SAFE_AUTO_ALLOWED and action.reversible:
                return (True, "safe-auto: low-risk reversible repair")
            return (False, "safe-auto: repair is not in the low-risk set")
        return (False, "no application mode")

    def set_mode(self, mode: str) -> None:
        if mode not in RepairPolicyMode.ALL:
            raise ValueError(f"unknown repair policy mode {mode!r}")
        self.mode = mode

    def snapshot(self) -> Dict[str, Any]:
        return {"mode": self.mode}
