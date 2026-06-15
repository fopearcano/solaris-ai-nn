"""Life cycle -- operational runtime phases over long horizons, not biological life.

The :class:`LifeCycleClock` advances a :class:`LifeCycleState` through bounded
operational phases (boot, baseline exposure, growth, consolidation, maturation
probe, plateau, regression watch, recovery, shutdown). "Life cycle" is operational
runtime language; it is NOT biological life. Every phase is bounded and leaves trace
evidence, and shutdown/restart are logged.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class LifeCyclePhase:
    BOOT = "boot"
    BASELINE_EXPOSURE = "baseline_exposure"
    SENSORY_ADAPTATION = "sensory_adaptation"
    CONCEPT_GROWTH = "concept_growth"
    SIGN_GROWTH = "sign_growth"
    COGNITIVE_STABILIZATION = "cognitive_stabilization"
    DESIRE_ACTION_LEARNING = "desire_action_learning"
    HABIT_CONSOLIDATION = "habit_consolidation"
    QUIET_CONSOLIDATION = "quiet_consolidation"
    LATENT_REPLAY = "latent_replay"
    MATURATION_PROBE = "maturation_probe"
    PLATEAU = "plateau"
    REGRESSION_WATCH = "regression_watch"
    RECOVERY = "recovery"
    SHUTDOWN = "shutdown"

    ALL = (BOOT, BASELINE_EXPOSURE, SENSORY_ADAPTATION, CONCEPT_GROWTH,
           SIGN_GROWTH, COGNITIVE_STABILIZATION, DESIRE_ACTION_LEARNING,
           HABIT_CONSOLIDATION, QUIET_CONSOLIDATION, LATENT_REPLAY,
           MATURATION_PROBE, PLATEAU, REGRESSION_WATCH, RECOVERY, SHUTDOWN)

    # The default progression order (each phase is bounded).
    ORDER = (BOOT, BASELINE_EXPOSURE, SENSORY_ADAPTATION, CONCEPT_GROWTH,
             SIGN_GROWTH, COGNITIVE_STABILIZATION, DESIRE_ACTION_LEARNING,
             HABIT_CONSOLIDATION, QUIET_CONSOLIDATION, MATURATION_PROBE)


@dataclass
class LifeCycleEvent:
    """One operational life-cycle event (phase entry / shutdown / restart)."""

    kind: str  # "phase_enter" | "shutdown" | "restart"
    phase: str
    tick: int = 0
    event_id: str = field(default_factory=lambda: f"LCE_{uuid.uuid4().hex[:8]}")
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "kind": self.kind,
                "phase": self.phase, "tick": self.tick,
                "evidence_refs": list(self.evidence_refs),
                "note": "operational runtime phase, not biological life"}


@dataclass
class LifeCycleState:
    """The current operational life-cycle phase and history (not biology)."""

    phase: str = LifeCyclePhase.BOOT
    events: List[LifeCycleEvent] = field(default_factory=list)
    restart_count: int = 0
    shutdown_count: int = 0

    @property
    def phases_visited(self) -> List[str]:
        return sorted({e.phase for e in self.events
                       if e.kind == "phase_enter"})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "phases_visited": self.phases_visited,
            "life_cycle_phase_count": len(self.phases_visited),
            "event_count": len(self.events),
            "restart_count": self.restart_count,
            "shutdown_count": self.shutdown_count,
            "note": "operational runtime life cycle; NOT biological life",
        }


@dataclass
class LifeCycleClock:
    """Advances the life-cycle phase; every phase is bounded and traced."""

    state: LifeCycleState = field(default_factory=LifeCycleState)

    def enter(self, phase: str, tick: int = 0,
              evidence_refs: List[str] = None) -> LifeCycleEvent:
        if phase not in LifeCyclePhase.ALL:
            phase = LifeCyclePhase.BOOT
        self.state.phase = phase
        ev = LifeCycleEvent(kind="phase_enter", phase=phase, tick=tick,
                            evidence_refs=list(evidence_refs or []))
        self.state.events.append(ev)
        return ev

    def advance(self, tick: int = 0) -> LifeCycleEvent:
        """Advance to the next phase in the default progression (then cycle)."""
        order = LifeCyclePhase.ORDER
        try:
            idx = order.index(self.state.phase)
            nxt = order[(idx + 1) % len(order)]
        except ValueError:
            nxt = LifeCyclePhase.BASELINE_EXPOSURE
        return self.enter(nxt, tick=tick)

    def restart(self, tick: int = 0) -> LifeCycleEvent:
        self.state.restart_count += 1
        ev = LifeCycleEvent(kind="restart", phase=self.state.phase, tick=tick)
        self.state.events.append(ev)
        return ev

    def shutdown(self, tick: int = 0) -> LifeCycleEvent:
        self.state.shutdown_count += 1
        self.state.phase = LifeCyclePhase.SHUTDOWN
        ev = LifeCycleEvent(kind="shutdown", phase=LifeCyclePhase.SHUTDOWN,
                            tick=tick)
        self.state.events.append(ev)
        return ev
