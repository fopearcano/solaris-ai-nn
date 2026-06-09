"""RuntimeLifecycle -- the NN lab's birth/death/continuity state machine.

This is *not* a copy of Solaris_Ai's Lifecycle. It is the lifecycle of a
Solaris-AI-NN experiment process, but it deliberately preserves the conceptual
vocabulary of birth, continuity, and death -- because treating shutdown as a
first-class "death" event (graceful or not) is exactly what lets us reason about
continuity gaps across restarts.

States:

    born -> running -> (sleeping <-> running) -> (checkpointing -> running)
                                                          -> dying -> dead

Transitions optionally write to a :class:`ContinuityLog`, so the lifecycle is
the single place that emits birth / heartbeat / checkpoint / death events.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from . import persistence as P
from .persistence import ContinuityLog

# Lifecycle state constants.
BORN = "born"
RUNNING = "running"
SLEEPING = "sleeping"
CHECKPOINTING = "checkpointing"
DYING = "dying"
DEAD = "dead"


@dataclass
class RuntimeLifecycle:
    """Tracks lifecycle state and stamps continuity events.

    Args:
        run_id: Stable brain identity (constant across restarts).
        session_id: Per-process session id.
        continuity_log: Optional log to record transitions into.
        is_restart: Whether this birth resumes a prior brain (logs ``restart``
            in addition to ``birth``).
    """

    run_id: str = ""
    session_id: str = ""
    continuity_log: Optional[ContinuityLog] = None
    is_restart: bool = False

    state: str = field(default=BORN, init=False)
    birth_ts: float = field(default=0.0, init=False)
    last_heartbeat_ts: float = field(default=0.0, init=False)
    last_heartbeat_step: int = field(default=0, init=False)
    death_ts: float = field(default=0.0, init=False)
    death_reason: str = field(default="", init=False)
    graceful: bool = field(default=False, init=False)

    def _log(self, event_type: str, message: str, step: int = 0, lifetime_step: int = 0,
             graceful: bool = True, **metadata: Any) -> None:
        if self.continuity_log is not None:
            self.continuity_log.log(
                event_type, message=message, step=step, lifetime_step=lifetime_step,
                graceful=graceful, **metadata,
            )

    # -- transitions --------------------------------------------------------

    def birth(self, lifetime_step: int = 0) -> None:
        """Enter the world: born -> running. Logs ``birth`` (and ``restart``)."""
        self.state = RUNNING
        self.birth_ts = time.time()
        self.last_heartbeat_ts = self.birth_ts
        if self.is_restart:
            self._log(P.RESTART, "resuming from persisted state", lifetime_step=lifetime_step)
        self._log(P.BIRTH, "lifecycle born", lifetime_step=lifetime_step)

    def heartbeat(self, step: int, lifetime_step: int = 0, log: bool = False) -> None:
        """Register a heartbeat tick, updating the last-heartbeat timestamp.

        ``log`` is throttled by the caller (the runner) so the continuity log is
        not flooded; the timestamp/step update happens every tick regardless so
        the brain-death gap is always accurate.
        """
        self.last_heartbeat_ts = time.time()
        self.last_heartbeat_step = step
        if self.state == SLEEPING:
            self.state = RUNNING
        if log:
            self._log(P.HEARTBEAT, "alive", step=step, lifetime_step=lifetime_step)

    def sleep(self, reason: str) -> None:
        """Pause activity (e.g. a silence window): running -> sleeping."""
        self.state = SLEEPING
        self._log(P.HEARTBEAT, f"sleep: {reason}", metadata_reason=reason)

    def wake(self, reason: str) -> None:
        """Resume activity: sleeping -> running."""
        self.state = RUNNING
        self._log(P.HEARTBEAT, f"wake: {reason}", metadata_reason=reason)

    def checkpoint(self, reason: str, step: int = 0, lifetime_step: int = 0,
                   **metadata: Any) -> None:
        """Mark a checkpoint: running -> checkpointing -> running. Logs ``checkpoint``."""
        prior = self.state
        self.state = CHECKPOINTING
        self._log(P.CHECKPOINT, reason, step=step, lifetime_step=lifetime_step, **metadata)
        self.state = RUNNING if prior != DEAD else DEAD

    def die(self, reason: str, graceful: bool = True, step: int = 0,
            lifetime_step: int = 0) -> None:
        """Terminate: -> dying -> dead. Logs ``graceful_death`` when graceful."""
        self.state = DYING
        self.death_ts = time.time()
        self.death_reason = reason
        self.graceful = graceful
        if graceful:
            self._log(P.GRACEFUL_DEATH, reason, step=step, lifetime_step=lifetime_step,
                      graceful=True)
        self.state = DEAD

    # -- inspection ---------------------------------------------------------

    def is_alive(self) -> bool:
        return self.state not in (DYING, DEAD)

    def snapshot(self) -> Dict[str, Any]:
        """Return a JSON-friendly view of the lifecycle's current state."""
        return {
            "state": self.state,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "is_restart": self.is_restart,
            "birth_ts": self.birth_ts,
            "last_heartbeat_ts": self.last_heartbeat_ts,
            "last_heartbeat_step": self.last_heartbeat_step,
            "death_ts": self.death_ts,
            "death_reason": self.death_reason,
            "graceful": self.graceful,
            "alive": self.is_alive(),
        }
