"""Auto-determination -- Being / Not-Being as an operational metric.

Solaris_Ai frames existence as a tension between Being and Not-Being. Here
that becomes two bounded pressures computed from concrete operational facts:
Being rises with fresh heartbeats, clean checkpoints, restored state, a
coherent Inner MAP, a stable world model, non-negative valence, and safe
operation; Not-Being rises with brain-death gaps, stale heartbeats, critical
incidents, unresolved Mysterium, repeated blocks, runaway/inert substrates,
failed checkpoints, policy violations, and exhaustion. The output is a
continuity metric and a *recommendation* -- it proves nothing metaphysical
and overrides nothing (governance and the ops watchdog stay in charge).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .variables import clamp01

# (context key, weight) contributing to each pressure.
BEING_FACTORS = (
    ("heartbeat_fresh", 1.0),
    ("continuity_stable", 1.0),
    ("checkpoint_ok", 0.8),
    ("state_restored", 0.6),
    ("inner_map_coherent", 0.6),
    ("world_model_stable", 0.5),
    ("valence_nonnegative", 0.6),
    ("safe_operation", 0.8),
    ("identity_continuity_ok", 0.6),  # ego (Prompt 18)
)

NOT_BEING_FACTORS = (
    ("brain_death_gap", 1.0),
    ("heartbeat_stale", 1.0),
    ("critical_incident", 1.0),
    ("mysterium_unresolved", 0.6),
    ("repeated_blocked_actions", 0.6),
    ("substrate_runaway", 0.8),
    ("substrate_inert", 0.8),
    ("checkpoint_failed", 0.8),
    ("policy_violation", 0.7),
    ("exhausted", 0.6),
    ("identity_anchor_mismatch", 0.7),  # ego (Prompt 18)
    ("ego_boundary_violation", 0.8),  # ego (Prompt 18)
)


class ActionImplication:
    CONTINUE = "continue"
    REST = "rest"
    CONSOLIDATE = "consolidate"
    REQUEST_REVIEW = "request_review"
    SAFE_SHUTDOWN_RECOMMENDED = "safe_shutdown_recommended"
    NO_ACTION = "no_action"

    ALL = (CONTINUE, REST, CONSOLIDATE, REQUEST_REVIEW,
           SAFE_SHUTDOWN_RECOMMENDED, NO_ACTION)


@dataclass
class BeingNotBeingTension:
    """One reading of the operational Being / Not-Being opposition."""

    being_pressure: float = 0.0
    not_being_pressure: float = 0.0
    tension: float = 0.0
    stability: float = 0.0
    action_implication: str = ActionImplication.NO_ACTION
    reasons: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    note: str = ("an operational continuity metric, not metaphysical proof "
                 "of existence; it cannot override governance")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AutoDeterminationState:
    """The tension over time."""

    current: BeingNotBeingTension = field(
        default_factory=BeingNotBeingTension)
    history: List[Dict[str, Any]] = field(default_factory=list)
    shutdown_recommendations: int = 0
    review_recommendations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current": self.current.to_dict(),
            "history_tail": self.history[-10:],
            "shutdown_recommendations": self.shutdown_recommendations,
            "review_recommendations": self.review_recommendations,
        }


@dataclass
class AutoDeterminationEngine:
    """Computes the tension from concrete operational context."""

    state: AutoDeterminationState = field(
        default_factory=AutoDeterminationState)

    def update(self, context: Optional[Dict[str, Any]] = None,
               ) -> BeingNotBeingTension:
        ctx = context or {}
        being_hits: List[str] = []
        being_total = 0.0
        being_weight = 0.0
        for key, weight in BEING_FACTORS:
            value = ctx.get(key)
            if value is None:
                continue
            being_weight += weight
            if bool(value):
                being_total += weight
                being_hits.append(key)
        not_hits: List[str] = []
        not_total = 0.0
        for key, weight in NOT_BEING_FACTORS:
            if bool(ctx.get(key)):
                not_total += weight
                not_hits.append(key)

        being = clamp01(being_total / being_weight) if being_weight else 0.0
        not_being = clamp01(not_total / 3.0)  # ~3 strong factors saturate
        # Tension is the live opposition: high when Not-Being presses
        # against an otherwise-living system.
        tension = round(clamp01(not_being * (0.5 + 0.5 * being)
                                + max(0.0, not_being - being) * 0.5), 4)
        stability = round(clamp01(being * (1.0 - not_being)), 4)

        implication, reasons = self._implication(being, not_being, ctx,
                                                 not_hits)
        reading = BeingNotBeingTension(
            being_pressure=round(being, 4),
            not_being_pressure=round(not_being, 4),
            tension=tension, stability=stability,
            action_implication=implication,
            reasons=reasons + [f"being: {', '.join(being_hits) or 'none'}",
                               f"not-being: {', '.join(not_hits) or 'none'}"])
        self.state.current = reading
        self.state.history.append({
            "being": reading.being_pressure,
            "not_being": reading.not_being_pressure,
            "tension": reading.tension,
            "implication": implication,
            "timestamp": reading.timestamp})
        self.state.history = self.state.history[-100:]
        if implication == ActionImplication.SAFE_SHUTDOWN_RECOMMENDED:
            self.state.shutdown_recommendations += 1
        elif implication == ActionImplication.REQUEST_REVIEW:
            self.state.review_recommendations += 1
        return reading

    @staticmethod
    def _implication(being: float, not_being: float,
                     ctx: Dict[str, Any],
                     not_hits: List[str]) -> "tuple[str, List[str]]":
        A = ActionImplication
        if not_being >= 0.7 or ctx.get("critical_incident"):
            return A.SAFE_SHUTDOWN_RECOMMENDED, [
                "not-being pressure is high; a graceful stop preserves "
                "continuity (a recommendation: ops decides)"]
        if not_being >= 0.45:
            return A.REQUEST_REVIEW, [
                "sustained not-being pressure deserves operator review"]
        if ctx.get("exhausted") or ctx.get("fatigue_high"):
            return A.REST, ["energy/fatigue pressure suggests rest"]
        if not_being >= 0.25:
            return A.CONSOLIDATE, [
                "mild not-being pressure; consolidation would help"]
        if being > 0.5:
            return A.CONTINUE, ["continuity is healthy"]
        return A.NO_ACTION, ["insufficient operational data"]

    def snapshot(self) -> Dict[str, Any]:
        return self.state.to_dict()
