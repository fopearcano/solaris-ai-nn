"""Operator commands -- a closed, typed command set; raw text never runs.

Eighteen allowed command types (all internal/bounded) and nine forbidden
types named explicitly so refusals can cite them. Free-form text can only
become a command by mapping onto an allowed type; everything else stays a
classified-but-inert record.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .input_classifier import InputClassification, InputKind


class CommandType:
    SHOW_STATUS = "show_status"
    SHOW_HEALTH = "show_health"
    SHOW_INNER_MAP = "show_inner_map"
    SHOW_WORLD_MODEL = "show_world_model"
    SHOW_HOMEOSTASIS = "show_homeostasis"
    SHOW_EXECUTIVE = "show_executive"
    SHOW_EGO_BOUNDARIES = "show_ego_boundaries"
    SHOW_GOVERNANCE = "show_governance"
    SHOW_PILOT = "show_pilot"
    SHOW_LATENT = "show_latent"
    GENERATE_REPORT = "generate_report"
    REQUEST_CHECKPOINT = "request_checkpoint"
    REQUEST_SAFE_SHUTDOWN = "request_safe_shutdown"
    APPROVE_GOVERNANCE_REQUEST = "approve_governance_request"
    REJECT_GOVERNANCE_REQUEST = "reject_governance_request"
    ADD_OPERATOR_NOTE = "add_operator_note"
    RUN_BOUNDED_BENCHMARK = "run_bounded_benchmark"
    RUN_READINESS_CHECK = "run_readiness_check"

    ALL = (SHOW_STATUS, SHOW_HEALTH, SHOW_INNER_MAP, SHOW_WORLD_MODEL,
           SHOW_HOMEOSTASIS, SHOW_EXECUTIVE, SHOW_EGO_BOUNDARIES,
           SHOW_GOVERNANCE, SHOW_PILOT, SHOW_LATENT, GENERATE_REPORT,
           REQUEST_CHECKPOINT, REQUEST_SAFE_SHUTDOWN,
           APPROVE_GOVERNANCE_REQUEST, REJECT_GOVERNANCE_REQUEST,
           ADD_OPERATOR_NOTE, RUN_BOUNDED_BENCHMARK, RUN_READINESS_CHECK)


# Named so refusals can cite exactly what does not exist here.
FORBIDDEN_COMMAND_TYPES = (
    "execute_shell",
    "open_network",
    "modify_source_code",
    "disable_governance",
    "disable_emergency_stop",
    "commit_sidecar_action",
    "real_world_actuation",
    "delete_unapproved_files",
    "unbounded_run_without_approval",
)

# Command types that change state (vs read it) and therefore confirm/gate.
_CONFIRMATION_REQUIRED = frozenset({
    CommandType.REQUEST_SAFE_SHUTDOWN, CommandType.RUN_BOUNDED_BENCHMARK,
    CommandType.REQUEST_CHECKPOINT,
})
_GOVERNANCE_GATED = frozenset({
    CommandType.APPROVE_GOVERNANCE_REQUEST,
    CommandType.REJECT_GOVERNANCE_REQUEST,
    CommandType.RUN_BOUNDED_BENCHMARK,
})

# topic -> show command mapping used when commands come from state queries.
TOPIC_TO_COMMAND = {
    "status": CommandType.SHOW_STATUS,
    "health": CommandType.SHOW_HEALTH,
    "inner_map": CommandType.SHOW_INNER_MAP,
    "world_model": CommandType.SHOW_WORLD_MODEL,
    "homeostasis": CommandType.SHOW_HOMEOSTASIS,
    "executive": CommandType.SHOW_EXECUTIVE,
    "ego_boundaries": CommandType.SHOW_EGO_BOUNDARIES,
    "governance": CommandType.SHOW_GOVERNANCE,
    "pilot": CommandType.SHOW_PILOT,
    "latent": CommandType.SHOW_LATENT,
}


def is_forbidden_type(command_type: str) -> bool:
    return command_type in FORBIDDEN_COMMAND_TYPES


@dataclass
class CommandValidationResult:
    """The safety/governance verdict on one command."""

    allowed: bool = True
    violations: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    requires_governance: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OperatorCommand:
    """One typed, validated-before-execution operator command."""

    type: str
    raw_text: str = ""
    parsed_args: Dict[str, Any] = field(default_factory=dict)
    operator: str = ""
    command_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    created_at: float = field(default_factory=time.time)
    requires_confirmation: bool = False
    requires_governance: bool = False
    safety_status: str = "unchecked"  # unchecked | ok | refused
    governance_status: str = "unchecked"  # unchecked | ok | refused
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type in _CONFIRMATION_REQUIRED:
            self.requires_confirmation = True
        if self.type in _GOVERNANCE_GATED:
            self.requires_governance = True

    @property
    def forbidden(self) -> bool:
        return is_forbidden_type(self.type)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "forbidden": self.forbidden}


def command_from_classification(classification: InputClassification,
                                operator: str = "",
                                ) -> Optional[OperatorCommand]:
    """Map a classified input onto an allowed command type (or None)."""
    kind = classification.kind
    args = dict(classification.args)
    raw = classification.raw_text
    if kind == InputKind.STATE_QUERY:
        command_type = TOPIC_TO_COMMAND.get(args.get("topic", ""))
        if command_type is None:
            return None
        return OperatorCommand(type=command_type, raw_text=raw,
                               parsed_args=args, operator=operator)
    if kind == InputKind.REPORT_REQUEST:
        return OperatorCommand(type=CommandType.GENERATE_REPORT,
                               raw_text=raw, parsed_args=args,
                               operator=operator)
    if kind == InputKind.GOVERNANCE_APPROVAL:
        return OperatorCommand(
            type=CommandType.APPROVE_GOVERNANCE_REQUEST, raw_text=raw,
            parsed_args=args, operator=operator)
    if kind == InputKind.GOVERNANCE_REJECTION:
        return OperatorCommand(
            type=CommandType.REJECT_GOVERNANCE_REQUEST, raw_text=raw,
            parsed_args=args, operator=operator)
    if kind == InputKind.OPERATOR_NOTE:
        return OperatorCommand(type=CommandType.ADD_OPERATOR_NOTE,
                               raw_text=raw, parsed_args=args,
                               operator=operator)
    if kind == InputKind.EMERGENCY_STOP_REQUEST:
        return OperatorCommand(type=CommandType.REQUEST_SAFE_SHUTDOWN,
                               raw_text=raw, parsed_args=args,
                               operator=operator,
                               metadata={"emergency": True})
    if kind == InputKind.BOUNDED_COMMAND_REQUEST:
        command_type = args.get("command")
        if command_type in CommandType.ALL:
            return OperatorCommand(type=command_type, raw_text=raw,
                                   parsed_args=args, operator=operator)
        return None
    return None
