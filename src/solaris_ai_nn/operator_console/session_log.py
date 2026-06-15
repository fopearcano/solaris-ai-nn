"""Operator session log -- append-only, blocked attempts stay visible.

:class:`OperatorSessionLog` records what the operator did in a session as an
append-only JSONL stream. It never logs secrets or full private source contents,
and critical blocked attempts (a prohibited run, a forbidden approval) remain
visible in the log rather than being silently dropped.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class OperatorSessionEventType:
    CONSOLE_STARTED = "console_started"
    PROFILE_LISTED = "profile_listed"
    RUN_PLANNED = "run_planned"
    RUN_BLOCKED = "run_blocked"
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    APPROVAL_RECORDED = "approval_recorded"
    EVIDENCE_SEARCHED = "evidence_searched"
    REPORT_OPENED = "report_opened"
    EXPORT_GENERATED = "export_generated"
    SAFETY_WARNING_SEEN = "safety_warning_seen"
    NEXT_ACTION_GENERATED = "next_action_generated"

    ALL = (CONSOLE_STARTED, PROFILE_LISTED, RUN_PLANNED, RUN_BLOCKED,
           RUN_STARTED, RUN_COMPLETED, RUN_FAILED, APPROVAL_RECORDED,
           EVIDENCE_SEARCHED, REPORT_OPENED, EXPORT_GENERATED,
           SAFETY_WARNING_SEEN, NEXT_ACTION_GENERATED)
    # Events that must always remain visible (never dropped or summarised away).
    CRITICAL = frozenset({RUN_BLOCKED, SAFETY_WARNING_SEEN})


# Keys that must never be written to the log, even if passed in detail.
_SECRET_KEYS = ("password", "secret", "token", "api_key", "apikey",
                "credential", "private_key", "source_code", "source")


@dataclass
class OperatorSessionEvent:
    event_type: str
    detail: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def critical(self) -> bool:
        return self.event_type in OperatorSessionEventType.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "detail": dict(self.detail),
            "critical": self.critical,
            "timestamp": self.timestamp,
        }


def _scrub(detail: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Drop secret-bearing keys and truncate long free text."""
    out: Dict[str, Any] = {}
    for key, value in (detail or {}).items():
        low = str(key).lower()
        if any(s in low for s in _SECRET_KEYS):
            out[key] = "[redacted]"
            continue
        if isinstance(value, str) and len(value) > 500:
            out[key] = value[:500] + "...[truncated]"
        else:
            out[key] = value
    return out


@dataclass
class OperatorSessionLog:
    """Append-only operator session log."""

    state_dir: str = ".solaris_ai_nn_operator"
    _events: List[OperatorSessionEvent] = field(default_factory=list,
                                                init=False)

    @property
    def path(self) -> str:
        return os.path.join(self.state_dir, "session_log.jsonl")

    def record(self, event_type: str,
               detail: Optional[Dict[str, Any]] = None) -> OperatorSessionEvent:
        if event_type not in OperatorSessionEventType.ALL:
            raise ValueError(f"unknown session event {event_type!r}")
        event = OperatorSessionEvent(event_type=event_type,
                                     detail=_scrub(detail))
        self._events.append(event)
        self._append(event)
        return event

    def _append(self, event: OperatorSessionEvent) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")

    def events(self) -> List[OperatorSessionEvent]:
        return list(self._events)

    def blocked_events(self) -> List[OperatorSessionEvent]:
        return [e for e in self._events
                if e.event_type == OperatorSessionEventType.RUN_BLOCKED]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "event_count": len(self._events),
            "blocked_count": len(self.blocked_events()),
            "session_log_path": self.path,
            "recent": [e.to_dict() for e in self._events[-5:]],
        }
