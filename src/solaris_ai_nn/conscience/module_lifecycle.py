"""Module lifecycle -- bounded, logged state transitions per module.

The :class:`ModuleLifecycleManager` moves modules through a small state
machine (unavailable -> registered -> configured -> initialized -> running ...
-> stopped) and logs every transition. A module failure marks it degraded or
failed and routes to ops/auto-regeneration; it does **not** crash the whole
runtime unless the module is critical.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ModuleLifecycleState:
    UNAVAILABLE = "unavailable"
    REGISTERED = "registered"
    CONFIGURED = "configured"
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPED = "stopped"

    ALL = (UNAVAILABLE, REGISTERED, CONFIGURED, INITIALIZED, RUNNING,
           PAUSED, DEGRADED, FAILED, STOPPED)


# transition name -> target state.
_TRANSITIONS = {
    "register": ModuleLifecycleState.REGISTERED,
    "configure": ModuleLifecycleState.CONFIGURED,
    "initialize": ModuleLifecycleState.INITIALIZED,
    "start": ModuleLifecycleState.RUNNING,
    "pause": ModuleLifecycleState.PAUSED,
    "resume": ModuleLifecycleState.RUNNING,
    "mark_degraded": ModuleLifecycleState.DEGRADED,
    "fail": ModuleLifecycleState.FAILED,
    "stop": ModuleLifecycleState.STOPPED,
    "safe_shutdown": ModuleLifecycleState.STOPPED,
}


@dataclass
class LifecycleTransition:
    """One logged transition for a module."""

    module: str
    transition: str
    from_state: str
    to_state: str
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ModuleLifecycleManager:
    """Drives and logs each module's lifecycle state."""

    states: Dict[str, str] = field(default_factory=dict)
    history: List[LifecycleTransition] = field(default_factory=list)

    def initial(self, module: str, available: bool) -> None:
        self.states[module] = (ModuleLifecycleState.REGISTERED if available
                               else ModuleLifecycleState.UNAVAILABLE)

    def transition(self, module: str, transition: str,
                   detail: str = "") -> str:
        if transition not in _TRANSITIONS:
            raise ValueError(f"unknown lifecycle transition {transition!r}")
        from_state = self.states.get(module,
                                     ModuleLifecycleState.UNAVAILABLE)
        # An unavailable module can only be (re)registered; otherwise it
        # stays unavailable.
        if from_state == ModuleLifecycleState.UNAVAILABLE \
                and transition != "register":
            return from_state
        to_state = _TRANSITIONS[transition]
        self.states[module] = to_state
        self.history.append(LifecycleTransition(
            module=module, transition=transition, from_state=from_state,
            to_state=to_state, detail=detail))
        self.history = self.history[-2000:]
        return to_state

    def mark_degraded(self, module: str, detail: str = "") -> str:
        return self.transition(module, "mark_degraded", detail)

    def fail(self, module: str, detail: str = "") -> str:
        return self.transition(module, "fail", detail)

    def safe_shutdown_all(self, reason: str = "") -> None:
        for module in list(self.states):
            if self.states[module] not in (
                    ModuleLifecycleState.UNAVAILABLE,
                    ModuleLifecycleState.STOPPED):
                self.transition(module, "safe_shutdown", reason)

    def degraded(self) -> List[str]:
        return sorted(m for m, s in self.states.items()
                      if s == ModuleLifecycleState.DEGRADED)

    def failed(self) -> List[str]:
        return sorted(m for m, s in self.states.items()
                      if s == ModuleLifecycleState.FAILED)

    def running(self) -> List[str]:
        return sorted(m for m, s in self.states.items()
                      if s == ModuleLifecycleState.RUNNING)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "states": dict(self.states),
            "running": self.running(),
            "degraded": self.degraded(),
            "failed": self.failed(),
            "transition_count": len(self.history),
            "recent": [t.to_dict() for t in self.history[-8:]],
        }
