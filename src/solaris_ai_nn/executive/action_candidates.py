"""Action candidates -- what the executive may suggest. Never commit.

Every candidate carries a typed executable scope (``none`` /
``simulation_only`` / ``internal_only`` / ``sidecar_suggestion_only``),
expected effect/cost/risk estimates, and ``committed=False`` -- structurally:
the field exists so the invariant is inspectable, and nothing in this layer
ever sets it true. ``no_action`` is always a valid candidate.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ActionCandidateType:
    SIMULATED_EMBODIED_ACTION = "simulated_embodied_action"
    INTERNAL_MAINTENANCE_ACTION = "internal_maintenance_action"
    LATENT_ACTION = "latent_action"
    SIDECAR_SUGGESTION = "sidecar_suggestion"
    OPERATOR_REVIEW_REQUEST = "operator_review_request"
    CHECKPOINT_REQUEST = "checkpoint_request"
    SAFE_SHUTDOWN_RECOMMENDATION = "safe_shutdown_recommendation"
    NO_ACTION = "no_action"

    ALL = (SIMULATED_EMBODIED_ACTION, INTERNAL_MAINTENANCE_ACTION,
           LATENT_ACTION, SIDECAR_SUGGESTION, OPERATOR_REVIEW_REQUEST,
           CHECKPOINT_REQUEST, SAFE_SHUTDOWN_RECOMMENDATION, NO_ACTION)


class ExecutableScope:
    NONE = "none"
    SIMULATION_ONLY = "simulation_only"
    INTERNAL_ONLY = "internal_only"
    SIDECAR_SUGGESTION_ONLY = "sidecar_suggestion_only"

    ALL = (NONE, SIMULATION_ONLY, INTERNAL_ONLY, SIDECAR_SUGGESTION_ONLY)


# Desire proposal (Prompt 16) -> (candidate type, executable scope).
PROPOSAL_TO_CANDIDATE = {
    "rest": (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
             ExecutableScope.SIMULATION_ONLY),
    "look": (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
             ExecutableScope.SIMULATION_ONLY),
    "seek_signal": (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                    ExecutableScope.SIMULATION_ONLY),
    "avoid_danger": (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                     ExecutableScope.SIMULATION_ONLY),
    "approach_reward": (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                        ExecutableScope.SIMULATION_ONLY),
    "explore_safely": (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                       ExecutableScope.SIMULATION_ONLY),
    "consolidate_memory": (ActionCandidateType.LATENT_ACTION,
                           ExecutableScope.INTERNAL_ONLY),
    "run_replay": (ActionCandidateType.LATENT_ACTION,
                   ExecutableScope.INTERNAL_ONLY),
    "reduce_activity": (ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
                        ExecutableScope.INTERNAL_ONLY),
    "stabilize": (ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
                  ExecutableScope.INTERNAL_ONLY),
    "remain_observe_only": (ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
                            ExecutableScope.INTERNAL_ONLY),
    "checkpoint_now": (ActionCandidateType.CHECKPOINT_REQUEST,
                       ExecutableScope.INTERNAL_ONLY),
    "request_operator_review": (ActionCandidateType.OPERATOR_REVIEW_REQUEST,
                                ExecutableScope.NONE),
    "safe_shutdown_recommended": (
        ActionCandidateType.SAFE_SHUTDOWN_RECOMMENDATION,
        ExecutableScope.NONE),
}


@dataclass
class ActionCandidate:
    """One suggestible action, fully accounted for."""

    action_type: str
    label: str
    source_desire_id: str = ""
    expected_effect: str = ""
    expected_cost: float = 0.0
    expected_risk: float = 0.0
    confidence: float = 0.5
    utility_estimate: float = 0.0
    safety_status: str = "ok"
    governance_status: str = "ok"
    executable_scope: str = ExecutableScope.NONE
    committed: bool = False  # always; this layer never commits anything
    inhibited: bool = False
    inhibition_reason: str = ""
    action_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action_type not in ActionCandidateType.ALL:
            raise ValueError(f"unknown action type {self.action_type!r}")
        if self.executable_scope not in ExecutableScope.ALL:
            raise ValueError(
                f"unknown executable scope {self.executable_scope!r}")
        if self.committed:
            raise ValueError("candidates are suggestions: committed must "
                             "stay False")
        if self.action_type == ActionCandidateType.SIDECAR_SUGGESTION \
                and self.executable_scope \
                != ExecutableScope.SIDECAR_SUGGESTION_ONLY:
            raise ValueError("sidecar candidates must carry the "
                             "sidecar_suggestion_only scope")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def no_action_candidate(reason: str = "no pressure demands action",
                        ) -> ActionCandidate:
    return ActionCandidate(
        action_type=ActionCandidateType.NO_ACTION, label="no_action",
        expected_effect=reason, expected_cost=0.0, expected_risk=0.0,
        confidence=0.9, utility_estimate=0.05,
        executable_scope=ExecutableScope.NONE)


# Per-label expected energy cost (rest is free, mirroring the action space).
LABEL_COSTS = {
    "rest": 0.0, "look": 0.05, "stabilize": 0.0, "reduce_activity": 0.0,
    "remain_observe_only": 0.0, "no_action": 0.0, "checkpoint_now": 0.05,
    "request_operator_review": 0.0, "safe_shutdown_recommended": 0.0,
    "consolidate_memory": 0.05, "run_replay": 0.1,
}


def candidate_from_desire(candidate: Any) -> ActionCandidate:
    """One Prompt-16 DesireCandidate -> one ActionCandidate."""
    proposal = getattr(candidate, "proposal", str(candidate))
    action_type, scope = PROPOSAL_TO_CANDIDATE.get(
        proposal, (ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
                   ExecutableScope.INTERNAL_ONLY))
    return ActionCandidate(
        action_type=action_type, label=proposal,
        source_desire_id=getattr(candidate, "proposal", ""),
        expected_effect=f"relieve {', '.join(getattr(candidate, 'source_needs', []) or ['(unknown need)'])}",
        expected_cost=LABEL_COSTS.get(
            proposal, 0.2 if scope == ExecutableScope.SIMULATION_ONLY
            else 0.05),
        confidence=float(getattr(candidate, "confidence", 0.5) or 0.5),
        utility_estimate=float(getattr(candidate, "motivation", 0.0) or 0.0),
        executable_scope=scope,
        inhibited=bool(getattr(candidate, "blocked", False)),
        inhibition_reason=str(getattr(candidate, "blocked_reason", "")),
        metadata={"source_needs": list(getattr(candidate, "source_needs",
                                               [])),
                  "source_drives": list(getattr(candidate, "source_drives",
                                                []))})


@dataclass
class ActionCandidateSet:
    """A batch of candidates plus the always-available no_action."""

    candidates: List[ActionCandidate] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not any(c.action_type == ActionCandidateType.NO_ACTION
                   for c in self.candidates):
            self.candidates.append(no_action_candidate())

    def active(self) -> List[ActionCandidate]:
        return [c for c in self.candidates if not c.inhibited]

    def inhibited(self) -> List[ActionCandidate]:
        return [c for c in self.candidates if c.inhibited]

    def by_label(self, label: str) -> Optional[ActionCandidate]:
        for candidate in self.candidates:
            if candidate.label == label:
                return candidate
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {"candidates": [c.to_dict() for c in self.candidates],
                "active": len(self.active()),
                "inhibited": len(self.inhibited())}
