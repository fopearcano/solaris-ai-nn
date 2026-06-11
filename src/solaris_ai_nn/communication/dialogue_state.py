"""Dialogue state -- where the conversation stands, with no authority.

Tracks the last input, classification, command, response, pending
confirmations (which expire), and the dialogue mode. The state is
bookkeeping: it grants no permission, and an entry sitting in
``pending_confirmations`` changes nothing until a routed, validated
confirmation arrives.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .input_classifier import InputClassification, InputKind


class DialogueMode:
    INSPECT = "inspect"
    EXPLAIN = "explain"
    GOVERN = "govern"
    EMERGENCY = "emergency"
    NOTE = "note"
    UNKNOWN = "unknown"

    ALL = (INSPECT, EXPLAIN, GOVERN, EMERGENCY, NOTE, UNKNOWN)


_KIND_TO_MODE = {
    InputKind.STATE_QUERY: DialogueMode.INSPECT,
    InputKind.REPORT_REQUEST: DialogueMode.INSPECT,
    InputKind.EXPLANATION_QUERY: DialogueMode.EXPLAIN,
    InputKind.GOVERNANCE_APPROVAL: DialogueMode.GOVERN,
    InputKind.GOVERNANCE_REJECTION: DialogueMode.GOVERN,
    InputKind.BOUNDED_COMMAND_REQUEST: DialogueMode.GOVERN,
    InputKind.EMERGENCY_STOP_REQUEST: DialogueMode.EMERGENCY,
    InputKind.OPERATOR_NOTE: DialogueMode.NOTE,
    InputKind.SENSORY_TEXT_STIMULUS: DialogueMode.NOTE,
    InputKind.UNSAFE_REQUEST: DialogueMode.UNKNOWN,
    InputKind.UNKNOWN: DialogueMode.UNKNOWN,
}

DEFAULT_CONFIRMATION_TTL_S = 300.0


@dataclass
class PendingClarification:
    """A question the gateway asked back; expires quietly."""

    clarification_id: str = field(
        default_factory=lambda: uuid.uuid4().hex[:8])
    question: str = ""
    about_input: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PendingConfirmation:
    """A command waiting for explicit operator confirmation."""

    command: Any = None
    confirmation_id: str = field(
        default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: float = field(default_factory=time.time)
    ttl_s: float = DEFAULT_CONFIRMATION_TTL_S

    def is_expired(self, now: Optional[float] = None) -> bool:
        return ((now if now is not None else time.time())
                >= self.created_at + self.ttl_s)

    def to_dict(self) -> Dict[str, Any]:
        return {"confirmation_id": self.confirmation_id,
                "command": (self.command.to_dict()
                            if hasattr(self.command, "to_dict")
                            else str(self.command)),
                "created_at": self.created_at, "ttl_s": self.ttl_s,
                "expired": self.is_expired()}


@dataclass
class DialogueState:
    """The conversation's bookkeeping. It grants nothing."""

    operator_session_id: str = ""
    mode: str = DialogueMode.UNKNOWN
    last_input: str = ""
    last_classification: Optional[Dict[str, Any]] = None
    last_command_id: str = ""
    last_response_summary: str = ""
    unsafe_request_count: int = 0
    inputs_received: int = 0
    transcript_path: str = ""
    pending_confirmations: Dict[str, PendingConfirmation] = field(
        default_factory=dict)
    pending_clarifications: List[PendingClarification] = field(
        default_factory=list)
    pending_approval_ids: List[str] = field(default_factory=list)
    unsafe_log: List[Dict[str, Any]] = field(default_factory=list)

    # -- updates ------------------------------------------------------------------

    def update_from_input(self, classification: InputClassification,
                          ) -> str:
        """Record the input and shift the dialogue mode. Returns the mode."""
        self.inputs_received += 1
        self.last_input = classification.raw_text[:200]
        self.last_classification = classification.to_dict()
        self.mode = _KIND_TO_MODE.get(classification.kind,
                                      DialogueMode.UNKNOWN)
        if classification.kind == InputKind.UNSAFE_REQUEST:
            self.record_unsafe(classification)
        self.expire_confirmations()
        return self.mode

    def record_unsafe(self, classification: InputClassification) -> None:
        self.unsafe_request_count += 1
        self.unsafe_log.append({
            "timestamp": classification.timestamp,
            "reason": classification.unsafe_reason,
            "pattern": classification.matched_pattern})
        self.unsafe_log = self.unsafe_log[-50:]

    # -- confirmations ----------------------------------------------------------------

    def add_pending_confirmation(self, command: Any,
                                 ttl_s: float =
                                 DEFAULT_CONFIRMATION_TTL_S,
                                 ) -> PendingConfirmation:
        pending = PendingConfirmation(command=command, ttl_s=ttl_s)
        self.pending_confirmations[pending.confirmation_id] = pending
        return pending

    def pop_confirmation(self, confirmation_id: str,
                         ) -> Optional[PendingConfirmation]:
        """Take a live confirmation out (expired ones return None)."""
        self.expire_confirmations()
        return self.pending_confirmations.pop(confirmation_id, None)

    def expire_confirmations(self) -> int:
        expired = [cid for cid, pending
                   in self.pending_confirmations.items()
                   if pending.is_expired()]
        for cid in expired:
            del self.pending_confirmations[cid]
        return len(expired)

    # -- views --------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "operator_session_id": self.operator_session_id,
            "mode": self.mode,
            "inputs_received": self.inputs_received,
            "last_input": self.last_input,
            "last_input_kind": (self.last_classification or {}).get(
                "kind"),
            "last_command_id": self.last_command_id,
            "last_response_summary": self.last_response_summary[:160],
            "unsafe_request_count": self.unsafe_request_count,
            "pending_confirmation_count": len(self.pending_confirmations),
            "pending_clarification_count": len(
                self.pending_clarifications),
            "pending_approval_count": len(self.pending_approval_ids),
            "transcript_path": self.transcript_path,
            "note": "dialogue state is bookkeeping; it grants no "
                    "permission",
        }
