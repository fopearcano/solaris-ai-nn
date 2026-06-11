"""Needs -- internal pressure estimates, never commands.

The NeedEstimator reads the homeostatic state (plus whatever context the
caller provides: Inner MAP, telemetry, world model, Mysterium, embodiment,
governance/ops status) and produces a NeedState: which pressures currently
exist, how intense and urgent they are, which variables they came from, and
which Desire proposals could relieve them. Needs feed Desire synthesis and
cannot override safety -- structurally, they are data.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .variables import HomeostaticState, clamp01


class NeedType:
    MAINTAIN_CONTINUITY = "maintain_continuity"
    RESTORE_ENERGY = "restore_energy"
    REDUCE_UNCERTAINTY = "reduce_uncertainty"
    SEEK_SIGNAL = "seek_signal"
    AVOID_DANGER = "avoid_danger"
    APPROACH_REWARD = "approach_reward"
    STABILIZE_AFTER_RESTART = "stabilize_after_restart"
    CONSOLIDATE_MEMORY = "consolidate_memory"
    PRUNE_REDUNDANCY = "prune_redundancy"
    INCREASE_EXPLORATION = "increase_exploration"
    INCREASE_STABILIZATION = "increase_stabilization"
    RESPECT_BOUNDARY = "respect_boundary"
    REQUEST_OPERATOR_REVIEW = "request_operator_review"
    REMAIN_OBSERVE_ONLY = "remain_observe_only"

    ALL = (MAINTAIN_CONTINUITY, RESTORE_ENERGY, REDUCE_UNCERTAINTY,
           SEEK_SIGNAL, AVOID_DANGER, APPROACH_REWARD,
           STABILIZE_AFTER_RESTART, CONSOLIDATE_MEMORY, PRUNE_REDUNDANCY,
           INCREASE_EXPLORATION, INCREASE_STABILIZATION, RESPECT_BOUNDARY,
           REQUEST_OPERATOR_REVIEW, REMAIN_OBSERVE_ONLY)


# Which Desire proposals could relieve each need (suggestions, not actions).
NEED_TO_DESIRES: Dict[str, List[str]] = {
    NeedType.MAINTAIN_CONTINUITY: ["checkpoint_now", "stabilize"],
    NeedType.RESTORE_ENERGY: ["rest", "reduce_activity"],
    NeedType.REDUCE_UNCERTAINTY: ["run_replay", "explore_safely", "look"],
    NeedType.SEEK_SIGNAL: ["seek_signal", "look"],
    NeedType.AVOID_DANGER: ["avoid_danger", "stabilize"],
    NeedType.APPROACH_REWARD: ["approach_reward"],
    NeedType.STABILIZE_AFTER_RESTART: ["stabilize", "checkpoint_now"],
    NeedType.CONSOLIDATE_MEMORY: ["consolidate_memory", "rest"],
    NeedType.PRUNE_REDUNDANCY: ["consolidate_memory"],
    NeedType.INCREASE_EXPLORATION: ["explore_safely", "look"],
    NeedType.INCREASE_STABILIZATION: ["stabilize", "reduce_activity"],
    NeedType.RESPECT_BOUNDARY: ["remain_observe_only", "stabilize"],
    NeedType.REQUEST_OPERATOR_REVIEW: ["request_operator_review"],
    NeedType.REMAIN_OBSERVE_ONLY: ["remain_observe_only"],
}


@dataclass
class Need:
    """One internal pressure estimate."""

    type: str
    intensity: float = 0.0
    urgency: float = 0.0
    source_variables: List[str] = field(default_factory=list)
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    possible_desires: List[str] = field(default_factory=list)
    inhibited_by: List[str] = field(default_factory=list)
    confidence: float = 0.0
    need_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in NeedType.ALL:
            raise ValueError(f"unknown need type {self.type!r}")
        if not self.possible_desires:
            self.possible_desires = list(NEED_TO_DESIRES.get(self.type, []))
        self.confidence = round(
            min(0.95, len(self.source_variables) / 3.0 + 0.2), 4)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class NeedState:
    """The current set of needs, dominant first."""

    needs: List[Need] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def dominant(self) -> Optional[Need]:
        if not self.needs:
            return None
        return max(self.needs, key=lambda n: (n.intensity, n.urgency,
                                              n.type))

    def by_type(self, need_type: str) -> Optional[Need]:
        for need in self.needs:
            if need.type == need_type:
                return need
        return None

    def to_dict(self) -> Dict[str, Any]:
        dominant = self.dominant()
        return {
            "needs": [n.to_dict() for n in sorted(
                self.needs, key=lambda n: (-n.intensity, n.type))],
            "dominant": dominant.type if dominant else None,
            "count": len(self.needs),
            "note": "needs are internal pressure estimates, not commands",
        }


# (need type, [(variable, threshold, invert)]): the need fires when any
# listed variable crosses its threshold (invert=True fires on LOW values).
_NEED_RULES = [
    (NeedType.MAINTAIN_CONTINUITY,
     [("heartbeat_freshness", 0.6, True), ("checkpoint_freshness", 0.5, True),
      ("operational_health", 0.6, True)]),
    (NeedType.STABILIZE_AFTER_RESTART,
     [("restart_stability", 0.6, True)]),
    (NeedType.RESTORE_ENERGY,
     [("body_energy", 0.35, True), ("fatigue", 0.6, False),
      ("exhaustion_pressure", 0.5, False), ("update_budget", 0.3, True)]),
    (NeedType.REDUCE_UNCERTAINTY,
     [("unknown_pressure", 0.5, False),
      ("prediction_miss_pressure", 0.5, False),
      ("world_unknown_ratio", 0.5, False),
      ("replay_mismatch_pressure", 0.5, False)]),
    (NeedType.SEEK_SIGNAL,
     [("low_stimulus_pressure", 0.5, False),
      ("external_signal_pressure", 0.1, True)]),
    (NeedType.AVOID_DANGER, [("danger_proximity", 0.5, False)]),
    (NeedType.APPROACH_REWARD, [("reward_proximity", 0.5, False)]),
    (NeedType.CONSOLIDATE_MEMORY,
     [("trace_pressure", 0.6, False), ("consolidation_pressure", 0.6,
                                       False)]),
    (NeedType.PRUNE_REDUNDANCY, [("graph_redundancy_pressure", 0.5,
                                  False)]),
    (NeedType.INCREASE_EXPLORATION, [("novelty_pressure", 0.1, True)]),
    (NeedType.INCREASE_STABILIZATION, [("novelty_pressure", 0.7, False)]),
    (NeedType.RESPECT_BOUNDARY,
     [("blocked_action_pressure", 0.4, False),
      ("policy_violation_pressure", 0.3, False),
      ("unsafe_proposal_pressure", 0.4, False),
      ("obstacle_pressure", 0.6, False),
      ("boundary_violation_pressure", 0.3, False),
      ("self_model_uncertainty_pressure", 0.4, False)]),
    (NeedType.REQUEST_OPERATOR_REVIEW,
     [("incident_pressure", 0.7, False), ("operator_pressure", 0.6,
                                          False),
      ("identity_uncertainty_pressure", 0.4, False)]),
]


@dataclass
class NeedEstimator:
    """Turns the homeostatic state (+ context) into a NeedState."""

    estimates_made: int = field(default=0, init=False)

    def estimate(self, state: HomeostaticState,
                 context: Optional[Dict[str, Any]] = None) -> NeedState:
        ctx = context or {}
        needs: List[Need] = []
        for need_type, rules in _NEED_RULES:
            sources: List[str] = []
            evidence: List[Dict[str, Any]] = []
            pressures: List[float] = []
            for variable_name, threshold, invert in rules:
                variable = state.get(variable_name)
                if variable is None:
                    continue
                fired = (variable.value < threshold if invert
                         else variable.value > threshold)
                if not fired:
                    continue
                pressure = (clamp01((threshold - variable.value)
                                    / max(threshold, 1e-9)) if invert
                            else clamp01((variable.value - threshold)
                                         / max(1.0 - threshold, 1e-9)))
                sources.append(variable_name)
                pressures.append(pressure)
                evidence.append({"variable": variable_name,
                                 "value": variable.value,
                                 "threshold": threshold,
                                 "trend": variable.trend})
            if not sources:
                continue
            intensity = clamp01(max(pressures))
            urgency = clamp01(max(state.get(v).urgency for v in sources))
            need = Need(type=need_type, intensity=round(intensity, 4),
                        urgency=round(urgency, 4),
                        source_variables=sources,
                        supporting_evidence=evidence)
            # The reward need is inhibited by exhaustion (recorded, not
            # silently dropped; the conflict resolver decides).
            if need_type == NeedType.APPROACH_REWARD \
                    and (state.value("exhaustion_pressure") > 0.5
                         or state.value("body_energy", 1.0) < 0.2):
                need.inhibited_by.append("exhaustion")
            needs.append(need)

        # Context-driven needs that are not variable thresholds.
        if ctx.get("sidecar_attached") or ctx.get("observe_only_required"):
            needs.append(Need(type=NeedType.REMAIN_OBSERVE_ONLY,
                              intensity=0.6, urgency=0.4,
                              source_variables=["sidecar_observation_"
                                                "pressure"],
                              supporting_evidence=[{"context":
                                                    "sidecar attached"}]))
        self.estimates_made += 1
        return NeedState(needs=needs)
