"""Governance audit -- every governance decision leaves a JSONL row.

This is the append-only trail that makes "who allowed what, when, and why"
answerable after the fact. Default location:
``.solaris_ai_nn_governance/governance_audit.jsonl``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

DEFAULT_GOVERNANCE_DIR = ".solaris_ai_nn_governance"
DEFAULT_AUDIT_PATH = f"{DEFAULT_GOVERNANCE_DIR}/governance_audit.jsonl"

POLICY_EVALUATED = "policy_evaluated"
POLICY_VIOLATION = "policy_violation"
APPROVAL_REQUESTED = "approval_requested"
APPROVAL_GRANTED = "approval_granted"
APPROVAL_REJECTED = "approval_rejected"
PERMISSION_CHECKED = "permission_checked"
RISK_ASSESSED = "risk_assessed"
EMERGENCY_STOP_REQUESTED = "emergency_stop_requested"
EMERGENCY_STOP_COMPLETED = "emergency_stop_completed"
OPERATOR_NOTE_ADDED = "operator_note_added"
RUNBOOK_GENERATED = "runbook_generated"
CHECKLIST_COMPLETED = "checklist_completed"

GOVERNANCE_AUDIT_EVENTS = frozenset({
    POLICY_EVALUATED, POLICY_VIOLATION,
    APPROVAL_REQUESTED, APPROVAL_GRANTED, APPROVAL_REJECTED,
    PERMISSION_CHECKED, RISK_ASSESSED,
    EMERGENCY_STOP_REQUESTED, EMERGENCY_STOP_COMPLETED,
    OPERATOR_NOTE_ADDED, RUNBOOK_GENERATED, CHECKLIST_COMPLETED,
})


@dataclass
class GovernanceAuditLog:
    """Append-only JSONL log of governance events (survives restarts)."""

    path: Union[str, Path] = DEFAULT_AUDIT_PATH
    run_id: str = ""
    session_id: str = ""
    operator: str = ""
    _writer: Any = field(default=None, repr=False, init=False)

    def __post_init__(self) -> None:
        from ..runtime.persistence import JsonlWriter  # local: avoid cycles

        self.path = Path(self.path)
        self._writer = JsonlWriter(self.path, append=True)

    def record(self, event_type: str, decision: str = "", reason: str = "",
               metadata: Optional[Dict[str, Any]] = None,
               operator: Optional[str] = None) -> Dict[str, Any]:
        """Append one governance event row; returns the row written."""
        if event_type not in GOVERNANCE_AUDIT_EVENTS:
            raise ValueError(f"unknown governance audit event {event_type!r}")
        row = {
            "timestamp": time.time(),
            "run_id": self.run_id,
            "session_id": self.session_id,
            "operator": operator if operator is not None else self.operator,
            "event_type": event_type,
            "decision": decision,
            "reason": reason,
            "metadata": metadata or {},
        }
        self._writer.write(row)
        return row

    def read_all(self) -> List[Dict[str, Any]]:
        from ..runtime.persistence import read_jsonl

        if not Path(self.path).exists():
            return []
        return list(read_jsonl(self.path))

    def count_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for row in self.read_all():
            key = row.get("event_type", "?")
            counts[key] = counts.get(key, 0) + 1
        return counts

    def last(self) -> Optional[Dict[str, Any]]:
        rows = self.read_all()
        return rows[-1] if rows else None

    def close(self) -> None:
        self._writer.close()
