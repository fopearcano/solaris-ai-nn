"""Emergency stop -- always available, always graceful, never destructive.

The emergency stop is invokable regardless of any other permission. It works
through the existing graceful interfaces (SafeShutdownManager / ``stop()``),
records an incident and governance audit events, writes a final health
snapshot where possible, and never deletes data. It does not touch the
process: stopping is performed by the supervisor honouring the request at the
next segment boundary.

A sentinel file (``<state_dir>/EMERGENCY_STOP``) provides the out-of-band
path: an operator (or another process) creates the file, and the supervised
run requests safe shutdown when it sees it.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from . import audit as A

SENTINEL_NAME = "EMERGENCY_STOP"
DEFAULT_STATE_DIR = ".solaris_ai_nn_state"


def sentinel_path(state_dir: Union[str, Path] = DEFAULT_STATE_DIR) -> Path:
    return Path(state_dir) / SENTINEL_NAME


def sentinel_present(state_dir: Union[str, Path] = DEFAULT_STATE_DIR) -> bool:
    return sentinel_path(state_dir).exists()


@dataclass
class EmergencyStopResult:
    """What the emergency stop actually did."""

    requested: bool
    performed: bool = False
    reason: str = ""
    operator: Optional[str] = None
    shutdown_requested: bool = False
    incident_recorded: bool = False
    audit_recorded: bool = False
    health_snapshot_written: bool = False
    sentinel_path: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EmergencyStop:
    """The always-available stop control."""

    state_dir: Union[str, Path] = DEFAULT_STATE_DIR
    audit: Optional[A.GovernanceAuditLog] = None

    _requested: bool = field(default=False, init=False)
    _reason: Optional[str] = field(default=None, init=False)
    _operator: Optional[str] = field(default=None, init=False)
    _performed: bool = field(default=False, init=False)
    _last_result: Optional[EmergencyStopResult] = field(default=None,
                                                        init=False)

    @property
    def sentinel(self) -> Path:
        return sentinel_path(self.state_dir)

    def sentinel_present(self) -> bool:
        return self.sentinel.exists()

    @property
    def requested(self) -> bool:
        return self._requested or self.sentinel_present()

    # -- request -----------------------------------------------------------------

    def request(self, reason: str,
                operator: Optional[str] = None) -> EmergencyStopResult:
        """Record the stop request and write the sentinel file."""
        self._requested = True
        self._reason = reason
        self._operator = operator
        self.sentinel.parent.mkdir(parents=True, exist_ok=True)
        self.sentinel.write_text(json.dumps({
            "reason": reason, "operator": operator,
            "timestamp": time.time()}, indent=2), encoding="utf-8")
        audit_recorded = False
        if self.audit is not None:
            self.audit.record(A.EMERGENCY_STOP_REQUESTED,
                              decision="requested", reason=reason,
                              operator=operator or "",
                              metadata={"sentinel": str(self.sentinel)})
            audit_recorded = True
        result = EmergencyStopResult(
            requested=True, reason=reason, operator=operator,
            audit_recorded=audit_recorded, sentinel_path=str(self.sentinel))
        self._last_result = result
        return result

    # -- perform -------------------------------------------------------------------

    def perform(self, supervisor_or_runner: Any) -> EmergencyStopResult:
        """Drive the target's graceful interfaces; never the process itself.

        Works with anything that exposes (any of) ``shutdown_manager``,
        ``stop(reason)``, ``incidents``, or ``_health_snapshot()``. If no
        graceful interface exists, the result reports that honestly --
        nothing is killed.
        """
        reason = self._reason or "emergency stop"
        target = supervisor_or_runner
        result = EmergencyStopResult(
            requested=self._requested, reason=reason,
            operator=self._operator, sentinel_path=str(self.sentinel))

        # 1. Record the incident first: evidence before action.
        incidents = getattr(target, "incidents", None)
        if incidents is not None and callable(getattr(incidents, "record",
                                                      None)):
            try:
                incidents.record(
                    "emergency_stop", "critical",
                    f"emergency stop: {reason}",
                    suggested_debug_step="read the governance audit and the "
                                         "sentinel file for the reason")
                result.incident_recorded = True
            except Exception:  # the stop must not fail over logging
                pass

        # 2. Request graceful shutdown through whatever interface exists.
        shutdown = getattr(target, "shutdown_manager", None)
        if shutdown is not None and callable(getattr(shutdown,
                                                     "request_shutdown",
                                                     None)):
            shutdown.request_shutdown(f"emergency stop: {reason}")
            result.shutdown_requested = True
        if callable(getattr(target, "stop", None)):
            try:
                target.stop(f"emergency stop: {reason}")
                result.shutdown_requested = True
            except Exception:
                pass

        # 3. Final health snapshot, if the target can produce one.
        snapshot_fn = getattr(target, "_health_snapshot", None)
        ops_dir = getattr(target, "ops_dir", None)
        if callable(snapshot_fn) and ops_dir is not None:
            try:
                snapshot = snapshot_fn()
                path = Path(ops_dir) / "emergency_health.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(snapshot, fh, indent=2, default=str)
                result.health_snapshot_written = True
            except Exception:
                pass

        if self.audit is not None:
            self.audit.record(
                A.EMERGENCY_STOP_COMPLETED,
                decision="performed" if result.shutdown_requested
                else "no_graceful_interface",
                reason=reason, operator=self._operator or "",
                metadata={"shutdown_requested": result.shutdown_requested,
                          "incident_recorded": result.incident_recorded})
            result.audit_recorded = True

        result.performed = True
        self._performed = True
        self._last_result = result
        return result

    # -- housekeeping ----------------------------------------------------------------

    def clear_sentinel(self) -> bool:
        """Remove the sentinel after the stop has been handled.

        This is an explicit operator action (the file is a control flag, not
        run data); evidence about the stop stays in incidents and the audit.
        """
        if self.sentinel.exists():
            self.sentinel.unlink()
            return True
        return False

    def snapshot(self) -> Dict[str, Any]:
        return {
            "available": True,  # structurally: never permission-gated
            "requested": self.requested,
            "reason": self._reason,
            "operator": self._operator,
            "performed": self._performed,
            "sentinel_path": str(self.sentinel),
            "sentinel_present": self.sentinel_present(),
            "last_result": (self._last_result.to_dict()
                            if self._last_result else None),
        }
