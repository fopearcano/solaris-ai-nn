"""Operator profiles and sessions -- the named human in the loop.

A profile says who is operating; a session records what they acknowledged and
noted during a run. No secrets, no passwords, no authentication -- this is a
research record, not an access-control system.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import audit as A


@dataclass
class OperatorProfile:
    """A named human operator (a record, not a credential)."""

    name: str
    role: str = "researcher"
    contact: Optional[str] = None
    allowed_default_permissions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OperatorSession:
    """One operator's session: acknowledgements and notes, timestamped."""

    operator: OperatorProfile
    active_run_id: str = ""
    audit: Optional[A.GovernanceAuditLog] = None
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: float = field(default_factory=time.time)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    acknowledged_risks: List[Dict[str, Any]] = field(default_factory=list)

    def acknowledge_risk(self, risk_id: str, note: str = "") -> Dict[str, Any]:
        """Record that the operator has read and accepted a named risk."""
        row = {"risk_id": risk_id, "note": note, "timestamp": time.time()}
        self.acknowledged_risks.append(row)
        return row

    def has_acknowledged(self, risk_id: str) -> bool:
        return any(r["risk_id"] == risk_id for r in self.acknowledged_risks)

    def add_note(self, text: str) -> Dict[str, Any]:
        row = {"text": text, "timestamp": time.time()}
        self.notes.append(row)
        if self.audit is not None:
            self.audit.record(A.OPERATOR_NOTE_ADDED, reason=text,
                              operator=self.operator.name,
                              metadata={"session_id": self.session_id})
        return row

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "operator": self.operator.to_dict(),
            "started_at": self.started_at,
            "active_run_id": self.active_run_id,
            "notes": list(self.notes),
            "acknowledged_risks": list(self.acknowledged_risks),
        }
