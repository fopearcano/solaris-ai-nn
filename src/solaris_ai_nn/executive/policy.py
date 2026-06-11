"""ExecutivePolicy -- which executive mode applies, ops and governance first.

Six modes: reactive_only, arbitrated (default), short_plan, observe_only,
latent_only, emergency. Ops status forces transitions (health critical or an
emergency stop forces ``emergency``; latent processing forces
``latent_only``), and the executive cannot talk itself out of emergency --
only ops/governance clearing the condition does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_candidates import ActionCandidateType


class ExecutiveMode:
    REACTIVE_ONLY = "reactive_only"
    ARBITRATED = "arbitrated"
    SHORT_PLAN = "short_plan"
    OBSERVE_ONLY = "observe_only"
    LATENT_ONLY = "latent_only"
    EMERGENCY = "emergency"

    ALL = (REACTIVE_ONLY, ARBITRATED, SHORT_PLAN, OBSERVE_ONLY,
           LATENT_ONLY, EMERGENCY)
    DEFAULT = ARBITRATED


# Which candidate types each mode permits.
MODE_ALLOWED_TYPES: Dict[str, frozenset] = {
    ExecutiveMode.REACTIVE_ONLY: frozenset({
        ActionCandidateType.SIMULATED_EMBODIED_ACTION,
        ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
        ActionCandidateType.NO_ACTION}),
    ExecutiveMode.ARBITRATED: frozenset(ActionCandidateType.ALL),
    ExecutiveMode.SHORT_PLAN: frozenset(ActionCandidateType.ALL),
    ExecutiveMode.OBSERVE_ONLY: frozenset({
        ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
        ActionCandidateType.OPERATOR_REVIEW_REQUEST,
        ActionCandidateType.CHECKPOINT_REQUEST,
        ActionCandidateType.NO_ACTION}),
    ExecutiveMode.LATENT_ONLY: frozenset({
        ActionCandidateType.LATENT_ACTION,
        ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
        ActionCandidateType.CHECKPOINT_REQUEST,
        ActionCandidateType.NO_ACTION}),
    ExecutiveMode.EMERGENCY: frozenset({
        ActionCandidateType.SAFE_SHUTDOWN_RECOMMENDATION,
        ActionCandidateType.OPERATOR_REVIEW_REQUEST,
        ActionCandidateType.CHECKPOINT_REQUEST,
        ActionCandidateType.NO_ACTION}),
}

LATENT_MODES = ("sleep", "dream", "replay", "consolidation",
                "wake_transition")


@dataclass
class ExecutivePolicy:
    """Determines and enforces the active executive mode."""

    requested_mode: str = ExecutiveMode.DEFAULT
    mode_changes: List[Dict[str, Any]] = field(default_factory=list,
                                               init=False)
    forced_emergency_total: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.requested_mode not in ExecutiveMode.ALL:
            raise ValueError(f"unknown executive mode "
                             f"{self.requested_mode!r}")
        self._current = self.requested_mode

    @property
    def mode(self) -> str:
        return self._current

    def determine_mode(self, context: Optional[Dict[str, Any]] = None,
                       ) -> str:
        """Ops and context override the requested mode; emergency wins."""
        ctx = context or {}
        previous = self._current
        if ctx.get("emergency") or ctx.get("emergency_stop_requested") \
                or ctx.get("health_level") == "critical":
            mode = ExecutiveMode.EMERGENCY
        elif ctx.get("watchdog_stop_requested") \
                or ctx.get("shutdown_requested"):
            mode = ExecutiveMode.EMERGENCY  # winding down: no new work
        elif str(ctx.get("latent_mode", "awake")) in LATENT_MODES:
            mode = ExecutiveMode.LATENT_ONLY
        elif ctx.get("observe_only"):
            mode = ExecutiveMode.OBSERVE_ONLY
        else:
            mode = self.requested_mode
        if mode != previous:
            self.mode_changes.append({"from": previous, "to": mode,
                                      "reason": self._reason(ctx, mode)})
            self.mode_changes = self.mode_changes[-50:]
            if mode == ExecutiveMode.EMERGENCY:
                self.forced_emergency_total += 1
        self._current = mode
        return mode

    @staticmethod
    def _reason(ctx: Dict[str, Any], mode: str) -> str:
        if mode == ExecutiveMode.EMERGENCY:
            return ("ops status forced emergency (critical health / stop "
                    "request); the executive cannot clear it")
        if mode == ExecutiveMode.LATENT_ONLY:
            return f"latent mode {ctx.get('latent_mode')!r} is active"
        if mode == ExecutiveMode.OBSERVE_ONLY:
            return "observe-only context"
        return "requested mode restored"

    def allows(self, action_type: str) -> bool:
        return action_type in MODE_ALLOWED_TYPES[self._current]

    def planning_allowed(self) -> bool:
        return self._current in (ExecutiveMode.SHORT_PLAN,)

    def execution_allowed(self) -> bool:
        """May a selected *simulated* action be executed by the simulation?"""
        return self._current in (ExecutiveMode.REACTIVE_ONLY,
                                 ExecutiveMode.ARBITRATED,
                                 ExecutiveMode.SHORT_PLAN)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "mode": self._current,
            "requested_mode": self.requested_mode,
            "forced_emergency_total": self.forced_emergency_total,
            "recent_changes": self.mode_changes[-5:],
            "allowed_types": sorted(MODE_ALLOWED_TYPES[self._current]),
        }
