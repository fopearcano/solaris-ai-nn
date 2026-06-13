"""Repair actions -- bounded, reversible requests to fix runtime state.

A :class:`RepairAction` repairs *runtime state* -- memory layers, registries,
world-model edges, habit weights, bounded runtime parameters, checkpoint
metadata, stale artifacts -- never source code. Every action carries a scope
(one of which is ``forbidden`` and never executes), a reversibility flag, and
its safety/governance status. Actions are suggestions until validated.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class RepairActionType:
    COMPACT_MEMORY_LAYER = "compact_memory_layer"
    ARCHIVE_OLD_TELEMETRY = "archive_old_telemetry"
    REBUILD_INDEX = "rebuild_index"
    REPAIR_BROKEN_REFERENCE = "repair_broken_reference"
    QUARANTINE_CORRUPT_RECORD = "quarantine_corrupt_record"
    RESTORE_FROM_CHECKPOINT = "restore_from_checkpoint"
    MARK_SYMBOL_STALE = "mark_symbol_stale"
    MERGE_DUPLICATE_SYMBOLS = "merge_duplicate_symbols"
    DECAY_RUNAWAY_HABIT = "decay_runaway_habit"
    RETIRE_DEAD_HABIT = "retire_dead_habit"
    WEAKEN_CONTRADICTORY_EDGE = "weaken_contradictory_edge"
    MARK_WORLD_EDGE_AMBIGUOUS = "mark_world_edge_ambiguous"
    REQUEST_CONSOLIDATION = "request_consolidation"
    REQUEST_LATENT_REPLAY = "request_latent_replay"
    REDUCE_SAMPLING_RATE = "reduce_sampling_rate"
    SWITCH_TO_STABILIZATION_MODE = "switch_to_stabilization_mode"
    RESET_BOUNDED_RUNTIME_PARAMETER = "reset_bounded_runtime_parameter"
    ROLLBACK_LAST_PLASTICITY_UPDATE = "rollback_last_plasticity_update"
    GENERATE_OPERATOR_REVIEW_REQUEST = "generate_operator_review_request"
    NO_REPAIR = "no_repair"

    ALL = (COMPACT_MEMORY_LAYER, ARCHIVE_OLD_TELEMETRY, REBUILD_INDEX,
           REPAIR_BROKEN_REFERENCE, QUARANTINE_CORRUPT_RECORD,
           RESTORE_FROM_CHECKPOINT, MARK_SYMBOL_STALE, MERGE_DUPLICATE_SYMBOLS,
           DECAY_RUNAWAY_HABIT, RETIRE_DEAD_HABIT, WEAKEN_CONTRADICTORY_EDGE,
           MARK_WORLD_EDGE_AMBIGUOUS, REQUEST_CONSOLIDATION,
           REQUEST_LATENT_REPLAY, REDUCE_SAMPLING_RATE,
           SWITCH_TO_STABILIZATION_MODE, RESET_BOUNDED_RUNTIME_PARAMETER,
           ROLLBACK_LAST_PLASTICITY_UPDATE,
           GENERATE_OPERATOR_REVIEW_REQUEST, NO_REPAIR)

    # Actions that only request another safe subsystem to act (no mutation).
    REQUEST_ONLY = frozenset({REQUEST_CONSOLIDATION, REQUEST_LATENT_REPLAY,
                              REDUCE_SAMPLING_RATE,
                              SWITCH_TO_STABILIZATION_MODE,
                              GENERATE_OPERATOR_REVIEW_REQUEST, NO_REPAIR})


class RepairScope:
    MEMORY = "memory"
    SYMBOL_REGISTRY = "symbol_registry"
    WORLD_MODEL = "world_model"
    HABIT_STATE = "habit_state"
    RUNTIME_PARAMETER = "runtime_parameter"
    CHECKPOINT_METADATA = "checkpoint_metadata"
    TELEMETRY_ARTIFACT = "telemetry_artifact"
    INDEX_REGISTRY = "index_registry"
    OPS_MODE = "ops_mode"
    FORBIDDEN = "forbidden"

    ALL = (MEMORY, SYMBOL_REGISTRY, WORLD_MODEL, HABIT_STATE,
           RUNTIME_PARAMETER, CHECKPOINT_METADATA, TELEMETRY_ARTIFACT,
           INDEX_REGISTRY, OPS_MODE, FORBIDDEN)
    RUNNABLE = frozenset({MEMORY, SYMBOL_REGISTRY, WORLD_MODEL, HABIT_STATE,
                          RUNTIME_PARAMETER, CHECKPOINT_METADATA,
                          TELEMETRY_ARTIFACT, INDEX_REGISTRY, OPS_MODE})


# Action type -> (scope, reversible, requires_governance default).
_ACTION_SPEC = {
    RepairActionType.COMPACT_MEMORY_LAYER: (RepairScope.MEMORY, True, False),
    RepairActionType.ARCHIVE_OLD_TELEMETRY: (
        RepairScope.TELEMETRY_ARTIFACT, True, False),
    RepairActionType.REBUILD_INDEX: (RepairScope.INDEX_REGISTRY, True, False),
    RepairActionType.REPAIR_BROKEN_REFERENCE: (
        RepairScope.INDEX_REGISTRY, True, False),
    RepairActionType.QUARANTINE_CORRUPT_RECORD: (
        RepairScope.TELEMETRY_ARTIFACT, True, False),
    RepairActionType.RESTORE_FROM_CHECKPOINT: (
        RepairScope.CHECKPOINT_METADATA, True, True),
    RepairActionType.MARK_SYMBOL_STALE: (
        RepairScope.SYMBOL_REGISTRY, True, False),
    RepairActionType.MERGE_DUPLICATE_SYMBOLS: (
        RepairScope.SYMBOL_REGISTRY, True, False),
    RepairActionType.DECAY_RUNAWAY_HABIT: (RepairScope.HABIT_STATE, True,
                                           False),
    RepairActionType.RETIRE_DEAD_HABIT: (RepairScope.HABIT_STATE, True, False),
    RepairActionType.WEAKEN_CONTRADICTORY_EDGE: (
        RepairScope.WORLD_MODEL, True, False),
    RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS: (
        RepairScope.WORLD_MODEL, True, False),
    RepairActionType.REQUEST_CONSOLIDATION: (RepairScope.MEMORY, True, False),
    RepairActionType.REQUEST_LATENT_REPLAY: (RepairScope.MEMORY, True, False),
    RepairActionType.REDUCE_SAMPLING_RATE: (RepairScope.OPS_MODE, True, False),
    RepairActionType.SWITCH_TO_STABILIZATION_MODE: (
        RepairScope.OPS_MODE, True, False),
    RepairActionType.RESET_BOUNDED_RUNTIME_PARAMETER: (
        RepairScope.RUNTIME_PARAMETER, True, False),
    RepairActionType.ROLLBACK_LAST_PLASTICITY_UPDATE: (
        RepairScope.RUNTIME_PARAMETER, True, False),
    RepairActionType.GENERATE_OPERATOR_REVIEW_REQUEST: (
        RepairScope.OPS_MODE, True, False),
    RepairActionType.NO_REPAIR: (RepairScope.OPS_MODE, True, False),
}


def spec_for(action_type: str) -> "tuple[str, bool, bool]":
    return _ACTION_SPEC.get(action_type, (RepairScope.OPS_MODE, True, False))


@dataclass
class RepairAction:
    """One bounded, auditable repair of runtime state (never source code)."""

    action_type: str
    scope: str = RepairScope.OPS_MODE
    target_ref: Optional[str] = None
    reason: str = ""
    expected_benefit: str = ""
    expected_risk: float = 0.05
    reversible: bool = True
    requires_governance: bool = False
    safety_status: str = "pending"
    governance_status: str = "pending"
    repair_id: str = field(default_factory=lambda: f"RPR_{uuid.uuid4().hex[:8]}")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action_type not in RepairActionType.ALL:
            raise ValueError(f"unknown repair action type "
                             f"{self.action_type!r}")
        if self.scope not in RepairScope.ALL:
            raise ValueError(f"unknown repair scope {self.scope!r}")
        self.expected_risk = max(0.0, min(1.0, float(self.expected_risk)))

    @property
    def is_request_only(self) -> bool:
        return self.action_type in RepairActionType.REQUEST_ONLY

    @property
    def is_runnable_scope(self) -> bool:
        return self.scope in RepairScope.RUNNABLE

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def make_repair(action_type: str, target_ref: Optional[str] = None,
                reason: str = "", expected_benefit: str = "",
                expected_risk: Optional[float] = None,
                **metadata: Any) -> RepairAction:
    """Build a RepairAction with the scope/reversibility for its type."""
    scope, reversible, requires_gov = spec_for(action_type)
    return RepairAction(
        action_type=action_type, scope=scope, target_ref=target_ref,
        reason=reason, expected_benefit=expected_benefit,
        expected_risk=(0.05 if expected_risk is None else expected_risk),
        reversible=reversible, requires_governance=requires_gov,
        metadata=dict(metadata))


# Repair action -> (executive label, candidate type, executable scope).
_CANDIDATE_MAP = {
    RepairActionType.REQUEST_LATENT_REPLAY: (
        "run_replay", "latent_action", "internal_only"),
    RepairActionType.REQUEST_CONSOLIDATION: (
        "consolidate_memory", "latent_action", "internal_only"),
    RepairActionType.COMPACT_MEMORY_LAYER: (
        "consolidate_memory", "latent_action", "internal_only"),
    RepairActionType.ROLLBACK_LAST_PLASTICITY_UPDATE: (
        "stabilize", "internal_maintenance_action", "internal_only"),
    RepairActionType.SWITCH_TO_STABILIZATION_MODE: (
        "stabilize", "internal_maintenance_action", "internal_only"),
    RepairActionType.REDUCE_SAMPLING_RATE: (
        "reduce_activity", "internal_maintenance_action", "internal_only"),
    RepairActionType.RESTORE_FROM_CHECKPOINT: (
        "checkpoint_now", "checkpoint_request", "internal_only"),
    RepairActionType.GENERATE_OPERATOR_REVIEW_REQUEST: (
        "request_operator_review", "operator_review_request", "none"),
    RepairActionType.NO_REPAIR: ("no_action", "no_action", "none"),
}


def repair_to_candidate(action: "RepairAction") -> Any:
    """One RepairAction -> one executive ActionCandidate (a suggestion).

    A repair enters executive arbitration like any other suggestion:
    inhibition applies and no unsafe repair can win. Nothing commits, and
    no repair reaches the real world or modifies source code.
    """
    from ..executive.action_candidates import ActionCandidate

    label, ctype, scope = _CANDIDATE_MAP.get(
        action.action_type,
        ("stabilize", "internal_maintenance_action", "internal_only"))
    return ActionCandidate(
        action_type=ctype, label=label,
        expected_effect=f"repair: {action.action_type} ({action.scope})",
        expected_cost=0.05, expected_risk=float(action.expected_risk),
        confidence=0.5, executable_scope=scope,
        metadata={"repair_id": action.repair_id,
                  "repair_action_type": action.action_type,
                  "repair_scope": action.scope,
                  "source": "autoregeneration"})


def no_repair(reason: str = "no repair needed or none safe") -> RepairAction:
    return RepairAction(
        action_type=RepairActionType.NO_REPAIR, scope=RepairScope.OPS_MODE,
        reason=reason, expected_risk=0.0, reversible=True,
        safety_status="ok", governance_status="ok")


class RepairResultClass:
    IMPROVED = "improved"
    NEUTRAL = "neutral"
    HARMFUL = "harmful"
    INCONCLUSIVE = "inconclusive"
    ROLLED_BACK = "rolled_back"
    REFUSED = "refused"

    ALL = (IMPROVED, NEUTRAL, HARMFUL, INCONCLUSIVE, ROLLED_BACK, REFUSED)


@dataclass
class RepairResult:
    """The outcome of (attempting) a repair action."""

    repair_id: str
    action_type: str
    scope: str
    applied: bool = False
    refused: bool = False
    refused_reason: str = ""
    rolled_back: bool = False
    result_class: str = RepairResultClass.INCONCLUSIVE
    before_metrics: Dict[str, Any] = field(default_factory=dict)
    after_metrics: Dict[str, Any] = field(default_factory=dict)
    detail: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)
