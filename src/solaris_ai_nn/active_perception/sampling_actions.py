"""Sampling actions -- how the system may choose to look at its world.

A :class:`SamplingAction` is a *suggestion* to sample the developmental
nursery, the simulated world, internal memory, a read-only stream, or a
sidecar observation. It is never a real-world action: every action carries a
:class:`SamplingScope` that is one of simulation-only, internal-only,
read-only-stream, sidecar-observe-only, or forbidden, and nothing here
commits anything. Executive arbitration and the safety validator decide
whether a proposed action may run at all.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class SamplingActionType:
    """The bounded vocabulary of self-directed sampling actions."""

    LOOK = "look"
    WAIT = "wait"
    REST = "rest"
    FOCUS_SIGNAL_SOURCE = "focus_signal_source"
    SAMPLE_BOUNDARY = "sample_boundary"
    SAMPLE_UNKNOWN_REGION = "sample_unknown_region"
    SAMPLE_KNOWN_PATTERN = "sample_known_pattern"
    SEEK_NOVELTY = "seek_novelty"
    SEEK_ABSENCE = "seek_absence"
    EMIT_SIMULATED_PING = "emit_simulated_ping"
    REPLAY_UNCERTAIN_TRACE = "replay_uncertain_trace"
    CONSOLIDATE_BEFORE_SAMPLING = "consolidate_before_sampling"
    INSPECT_WORLD_MODEL_NODE = "inspect_world_model_node"
    INSPECT_PROTO_SYMBOL = "inspect_proto_symbol"
    OBSERVE_SIDECAR_ONLY = "observe_sidecar_only"
    NO_SAMPLING_ACTION = "no_sampling_action"

    ALL = (LOOK, WAIT, REST, FOCUS_SIGNAL_SOURCE, SAMPLE_BOUNDARY,
           SAMPLE_UNKNOWN_REGION, SAMPLE_KNOWN_PATTERN, SEEK_NOVELTY,
           SEEK_ABSENCE, EMIT_SIMULATED_PING, REPLAY_UNCERTAIN_TRACE,
           CONSOLIDATE_BEFORE_SAMPLING, INSPECT_WORLD_MODEL_NODE,
           INSPECT_PROTO_SYMBOL, OBSERVE_SIDECAR_ONLY, NO_SAMPLING_ACTION)

    # Actions that only ever touch internal/offline state.
    INTERNAL = frozenset({REPLAY_UNCERTAIN_TRACE,
                          CONSOLIDATE_BEFORE_SAMPLING,
                          INSPECT_WORLD_MODEL_NODE, INSPECT_PROTO_SYMBOL,
                          REST, WAIT, NO_SAMPLING_ACTION})
    # Actions that touch the simulated world / nursery.
    SIMULATED = frozenset({LOOK, FOCUS_SIGNAL_SOURCE, SAMPLE_BOUNDARY,
                           SAMPLE_UNKNOWN_REGION, SAMPLE_KNOWN_PATTERN,
                           SEEK_NOVELTY, SEEK_ABSENCE, EMIT_SIMULATED_PING})


class SamplingScope:
    """Where a sampling action is permitted to reach (never the real world)."""

    SIMULATION_ONLY = "simulation_only"
    INTERNAL_ONLY = "internal_only"
    READ_ONLY_STREAM = "read_only_stream"
    SIDECAR_OBSERVE_ONLY = "sidecar_observe_only"
    FORBIDDEN = "forbidden"

    ALL = (SIMULATION_ONLY, INTERNAL_ONLY, READ_ONLY_STREAM,
           SIDECAR_OBSERVE_ONLY, FORBIDDEN)
    # Scopes a proposed action may carry and still be runnable.
    RUNNABLE = frozenset({SIMULATION_ONLY, INTERNAL_ONLY,
                          READ_ONLY_STREAM, SIDECAR_OBSERVE_ONLY})


# Pressure tags that may motivate a sampling action (provenance only).
class SamplingPressure:
    MYSTERIUM = "mysterium"
    PREDICTION_ERROR = "prediction_error"
    HOMEOSTASIS = "homeostasis"
    WORLD_MODEL_UNCERTAINTY = "world_model_uncertainty"
    PROTO_SYMBOL_AMBIGUITY = "proto_symbol_ambiguity"
    DEVELOPMENTAL_STAGNATION = "developmental_stagnation"
    ECOLOGY_CYCLE = "ecology_cycle"
    SAFETY = "safety"

    ALL = (MYSTERIUM, PREDICTION_ERROR, HOMEOSTASIS,
           WORLD_MODEL_UNCERTAINTY, PROTO_SYMBOL_AMBIGUITY,
           DEVELOPMENTAL_STAGNATION, ECOLOGY_CYCLE, SAFETY)


# Default scope for each action type (the most reach it may ever request).
_DEFAULT_SCOPE = {
    SamplingActionType.LOOK: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.WAIT: SamplingScope.INTERNAL_ONLY,
    SamplingActionType.REST: SamplingScope.INTERNAL_ONLY,
    SamplingActionType.FOCUS_SIGNAL_SOURCE: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.SAMPLE_BOUNDARY: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.SAMPLE_UNKNOWN_REGION: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.SAMPLE_KNOWN_PATTERN: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.SEEK_NOVELTY: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.SEEK_ABSENCE: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.EMIT_SIMULATED_PING: SamplingScope.SIMULATION_ONLY,
    SamplingActionType.REPLAY_UNCERTAIN_TRACE: SamplingScope.INTERNAL_ONLY,
    SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING:
        SamplingScope.INTERNAL_ONLY,
    SamplingActionType.INSPECT_WORLD_MODEL_NODE: SamplingScope.INTERNAL_ONLY,
    SamplingActionType.INSPECT_PROTO_SYMBOL: SamplingScope.INTERNAL_ONLY,
    SamplingActionType.OBSERVE_SIDECAR_ONLY:
        SamplingScope.SIDECAR_OBSERVE_ONLY,
    SamplingActionType.NO_SAMPLING_ACTION: SamplingScope.INTERNAL_ONLY,
}


def default_scope(action_type: str) -> str:
    return _DEFAULT_SCOPE.get(action_type, SamplingScope.INTERNAL_ONLY)


# Sampling action -> the executive's recognized action label (so executive
# inhibition can reason about a sampling candidate). The sampling action id
# is preserved in candidate metadata; this is only the arbitration label.
_EXECUTIVE_LABEL = {
    SamplingActionType.LOOK: "look",
    SamplingActionType.WAIT: "remain_observe_only",
    SamplingActionType.REST: "rest",
    SamplingActionType.FOCUS_SIGNAL_SOURCE: "look",
    SamplingActionType.SAMPLE_BOUNDARY: "look",
    SamplingActionType.SAMPLE_UNKNOWN_REGION: "explore_safely",
    SamplingActionType.SAMPLE_KNOWN_PATTERN: "look",
    SamplingActionType.SEEK_NOVELTY: "explore_safely",
    SamplingActionType.SEEK_ABSENCE: "reduce_activity",
    SamplingActionType.EMIT_SIMULATED_PING: "emit_ping",
    SamplingActionType.REPLAY_UNCERTAIN_TRACE: "run_replay",
    SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING: "consolidate_memory",
    SamplingActionType.INSPECT_WORLD_MODEL_NODE: "look",
    SamplingActionType.INSPECT_PROTO_SYMBOL: "look",
    SamplingActionType.OBSERVE_SIDECAR_ONLY: "remain_observe_only",
    SamplingActionType.NO_SAMPLING_ACTION: "no_action",
}


@dataclass
class SamplingAction:
    """One proposed self-directed sampling action (a suggestion, never a
    committed real-world action)."""

    action_type: str
    scope: str = SamplingScope.INTERNAL_ONLY
    target_ref: Optional[str] = None
    expected_information_gain: float = 0.0
    expected_cost: float = 0.0
    expected_risk: float = 0.0
    source_pressure: str = SamplingPressure.MYSTERIUM
    confidence: float = 0.5
    safety_status: str = "pending"
    governance_status: str = "pending"
    action_id: str = field(default_factory=lambda: f"SMP_{uuid.uuid4().hex[:8]}")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action_type not in SamplingActionType.ALL:
            raise ValueError(f"unknown sampling action type "
                             f"{self.action_type!r}")
        if self.scope not in SamplingScope.ALL:
            raise ValueError(f"unknown sampling scope {self.scope!r}")
        self.expected_information_gain = max(
            0.0, min(1.0, float(self.expected_information_gain)))
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    @property
    def is_internal_only(self) -> bool:
        return self.scope == SamplingScope.INTERNAL_ONLY

    @property
    def is_observe_only(self) -> bool:
        return self.scope == SamplingScope.SIDECAR_OBSERVE_ONLY

    @property
    def is_runnable_scope(self) -> bool:
        return self.scope in SamplingScope.RUNNABLE

    def can_publish_suggestions(self) -> bool:
        """observe_sidecar_only can never publish or commit."""
        return False

    def can_modify_input_stream(self) -> bool:
        """read_only_stream can never modify the stream."""
        return False

    def to_action_candidate(self) -> Any:
        """One SamplingAction -> one executive ActionCandidate (suggestion).

        Sampling actions enter executive arbitration like any other
        suggestion: inhibition applies, prospection estimates consequences,
        and no unsafe action can win. The candidate never commits.
        """
        from ..executive.action_candidates import (
            ActionCandidate,
            ActionCandidateType,
            ExecutableScope,
        )

        latent_types = {SamplingActionType.REPLAY_UNCERTAIN_TRACE,
                        SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING}
        if self.action_type == SamplingActionType.NO_SAMPLING_ACTION:
            ctype, cscope = (ActionCandidateType.NO_ACTION,
                             ExecutableScope.NONE)
        elif self.scope == SamplingScope.SIMULATION_ONLY:
            ctype, cscope = (ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                             ExecutableScope.SIMULATION_ONLY)
        elif self.action_type in latent_types:
            ctype, cscope = (ActionCandidateType.LATENT_ACTION,
                             ExecutableScope.INTERNAL_ONLY)
        else:
            ctype, cscope = (ActionCandidateType.INTERNAL_MAINTENANCE_ACTION,
                             ExecutableScope.INTERNAL_ONLY)
        # The executive recognizes a fixed action vocabulary; map the
        # sampling action onto it so inhibition can reason about it (the
        # original sampling action id is preserved in metadata).
        label = _EXECUTIVE_LABEL.get(self.action_type, "look")
        return ActionCandidate(
            action_type=ctype, label=label,
            expected_effect=f"sample to relieve {self.source_pressure}",
            expected_cost=float(self.expected_cost),
            expected_risk=float(self.expected_risk),
            confidence=float(self.confidence),
            utility_estimate=float(self.expected_information_gain),
            executable_scope=cscope,
            metadata={"sampling_action_id": self.action_id,
                      "source_pressure": self.source_pressure,
                      "sampling_scope": self.scope,
                      "source": "active_perception"})

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def no_sampling_action(reason: str = "no safe sampling action available",
                       ) -> SamplingAction:
    """The always-valid fallback: choose not to sample."""
    return SamplingAction(
        action_type=SamplingActionType.NO_SAMPLING_ACTION,
        scope=SamplingScope.INTERNAL_ONLY,
        expected_information_gain=0.0, expected_cost=0.0,
        expected_risk=0.0, confidence=0.9,
        safety_status="ok", governance_status="ok",
        metadata={"reason": reason})


@dataclass
class SamplingActionResult:
    """The observed outcome of (attempting) a sampling action."""

    action_id: str
    action_type: str
    scope: str
    executed: bool = False
    blocked: bool = False
    blocked_reason: str = ""
    observed_information_gain: float = 0.0
    cost: float = 0.0
    outcome: str = "unknown"  # useful | neutral | harmful | unknown | blocked
    safety_status: str = "ok"
    detail: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)
