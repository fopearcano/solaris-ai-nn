"""Motor action schema -- what Solaris-AI-NN *would* do, simulation-only.

A :class:`MotorAction` is an *intention*, never permission to act. Every motor
action carries ``real_world_authority = False`` and a scope that is internal /
simulation / dry-run / sandbox / read-only-observation -- real-world scopes are
representable only as *forbidden/blocked*. Action records are audit trail, not
authority.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class MotorActionType:
    WAIT = "wait"
    REST = "rest"
    LOOK = "look"
    MOVE_NORTH = "move_north"
    MOVE_SOUTH = "move_south"
    MOVE_EAST = "move_east"
    MOVE_WEST = "move_west"
    APPROACH_SIGNAL = "approach_signal"
    AVOID_SIGNAL = "avoid_signal"
    INSPECT_BOUNDARY = "inspect_boundary"
    EMIT_SIMULATED_PING = "emit_simulated_ping"
    TOUCH_SIMULATED_OBJECT = "touch_simulated_object"
    PICK_SIMULATED_OBJECT = "pick_simulated_object"
    DROP_SIMULATED_OBJECT = "drop_simulated_object"
    MARK_SIMULATED_LOCATION = "mark_simulated_location"
    REQUEST_CONSOLIDATION = "request_consolidation"
    REQUEST_REPLAY = "request_replay"
    NO_ACTION = "no_action"

    ALL = (WAIT, REST, LOOK, MOVE_NORTH, MOVE_SOUTH, MOVE_EAST, MOVE_WEST,
           APPROACH_SIGNAL, AVOID_SIGNAL, INSPECT_BOUNDARY,
           EMIT_SIMULATED_PING, TOUCH_SIMULATED_OBJECT, PICK_SIMULATED_OBJECT,
           DROP_SIMULATED_OBJECT, MARK_SIMULATED_LOCATION,
           REQUEST_CONSOLIDATION, REQUEST_REPLAY, NO_ACTION)
    # GridWorld-handled simulated movement/interaction actions.
    GRIDWORLD = frozenset({LOOK, MOVE_NORTH, MOVE_SOUTH, MOVE_EAST, MOVE_WEST,
                           APPROACH_SIGNAL, AVOID_SIGNAL, INSPECT_BOUNDARY,
                           EMIT_SIMULATED_PING, TOUCH_SIMULATED_OBJECT,
                           PICK_SIMULATED_OBJECT, DROP_SIMULATED_OBJECT,
                           MARK_SIMULATED_LOCATION, WAIT, REST})
    # Internal-only actions (no body needed).
    INTERNAL = frozenset({WAIT, REST, NO_ACTION, REQUEST_CONSOLIDATION,
                          REQUEST_REPLAY})


class MotorActionScope:
    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    DRY_RUN_ONLY = "dry_run_only"
    SANDBOX_ONLY = "sandbox_only"
    READ_ONLY_OBSERVATION = "read_only_observation"
    FORBIDDEN_REAL_WORLD = "forbidden_real_world"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, DRY_RUN_ONLY, SANDBOX_ONLY,
           READ_ONLY_OBSERVATION, FORBIDDEN_REAL_WORLD)
    # Scopes a motor action may actually run under (never real-world).
    RUNNABLE = frozenset({INTERNAL_ONLY, SIMULATION_ONLY, DRY_RUN_ONLY,
                          SANDBOX_ONLY, READ_ONLY_OBSERVATION})


class MotorActionStatus:
    PROPOSED = "proposed"
    VETOED = "vetoed"
    APPROVED_FOR_SIMULATION = "approved_for_simulation"
    EXECUTED_IN_SIMULATION = "executed_in_simulation"
    DRY_RUN_RECORDED = "dry_run_recorded"
    BLOCKED_BY_FIREWALL = "blocked_by_firewall"
    BLOCKED_BY_GOVERNANCE = "blocked_by_governance"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    FAILED = "failed"
    COMPLETED = "completed"

    ALL = (PROPOSED, VETOED, APPROVED_FOR_SIMULATION, EXECUTED_IN_SIMULATION,
           DRY_RUN_RECORDED, BLOCKED_BY_FIREWALL, BLOCKED_BY_GOVERNANCE,
           BLOCKED_BY_SAFETY, FAILED, COMPLETED)
    BLOCKED = frozenset({VETOED, BLOCKED_BY_FIREWALL, BLOCKED_BY_GOVERNANCE,
                         BLOCKED_BY_SAFETY})


@dataclass
class MotorAction:
    """One motor intention -- never permission to act on the real world."""

    action_type: str
    scope: str = MotorActionScope.SIMULATION_ONLY
    source_desire_ref: Optional[str] = None
    source_candidate_ref: Optional[str] = None
    target_ref: Optional[str] = None
    expected_effect: str = ""
    expected_information_gain: float = 0.0
    expected_cost: float = 0.0
    expected_risk: float = 0.0
    simulated_only: bool = True
    real_world_authority: bool = False
    safety_status: str = "unchecked"
    governance_status: str = "unchecked"
    ego_boundary_status: str = "unchecked"
    status: str = MotorActionStatus.PROPOSED
    action_id: str = field(default_factory=lambda: f"ACT_{uuid.uuid4().hex[:10]}")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action_type not in MotorActionType.ALL:
            self.action_type = MotorActionType.NO_ACTION
        if self.scope not in MotorActionScope.ALL:
            self.scope = MotorActionScope.FORBIDDEN_REAL_WORLD
        # Invariants: a motor action never has real-world authority.
        self.real_world_authority = False
        self.simulated_only = True

    @property
    def is_real_world_scope(self) -> bool:
        return self.scope == MotorActionScope.FORBIDDEN_REAL_WORLD

    @property
    def is_runnable_scope(self) -> bool:
        return self.scope in MotorActionScope.RUNNABLE

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "is_real_world_scope": self.is_real_world_scope,
                "is_runnable_scope": self.is_runnable_scope}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MotorAction":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class MotorActionResult:
    """The outcome of a (simulated/dry-run) motor action."""

    action_id: str
    action_type: str
    status: str
    simulated: bool = True
    real_world_authority: bool = False
    effect_summary: str = ""
    reaction_valence: float = 0.0
    information_gain: float = 0.0
    evidence_refs: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)
