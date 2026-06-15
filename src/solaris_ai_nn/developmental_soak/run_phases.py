"""Soak run phases -- the bounded, explainable per-cycle phase sequence.

Each soak invocation walks a bounded sequence of run phases (boot ->
baseline_capture -> active_developmental_cycle -> quiet_consolidation ->
checkpoint -> safety_scan -> daily_packet -> weekly_review -> restart_drill ->
phase_summary -> shutdown_or_continue). Every phase writes trace evidence; every
transition is explainable; every failure is recorded (never hidden).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SoakRunPhase:
    BOOT = "boot"
    BASELINE_CAPTURE = "baseline_capture"
    ACTIVE_DEVELOPMENTAL_CYCLE = "active_developmental_cycle"
    QUIET_CONSOLIDATION = "quiet_consolidation"
    CHECKPOINT = "checkpoint"
    SAFETY_SCAN = "safety_scan"
    DAILY_PACKET = "daily_packet"
    WEEKLY_REVIEW = "weekly_review"
    RESTART_DRILL = "restart_drill"
    PHASE_SUMMARY = "phase_summary"
    SHUTDOWN_OR_CONTINUE = "shutdown_or_continue"

    ORDER = (BOOT, BASELINE_CAPTURE, ACTIVE_DEVELOPMENTAL_CYCLE,
             QUIET_CONSOLIDATION, CHECKPOINT, SAFETY_SCAN, DAILY_PACKET,
             WEEKLY_REVIEW, RESTART_DRILL, PHASE_SUMMARY, SHUTDOWN_OR_CONTINUE)


@dataclass
class SoakPhaseTransition:
    """An explainable transition between two run phases."""

    from_phase: Optional[str]
    to_phase: str
    reason: str
    tick: int = 0
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"from_phase": self.from_phase, "to_phase": self.to_phase,
                "reason": self.reason, "tick": self.tick, "ts": self.ts,
                "explainable": True}


@dataclass
class SoakPhaseFailure:
    phase: str
    reason: str
    tick: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"phase": self.phase, "reason": self.reason, "tick": self.tick}


@dataclass
class SoakPhaseState:
    """Tracks the current phase, transitions, failures, and trace evidence."""

    current_phase: Optional[str] = None
    transitions: List[SoakPhaseTransition] = field(default_factory=list)
    failures: List[SoakPhaseFailure] = field(default_factory=list)
    trace: List[Dict[str, Any]] = field(default_factory=list)
    phases_run: List[str] = field(default_factory=list)

    def enter(self, phase: str, reason: str, *, tick: int = 0) -> None:
        if phase not in SoakRunPhase.ORDER:
            raise ValueError(f"unknown soak run phase {phase!r}")
        self.transitions.append(SoakPhaseTransition(
            from_phase=self.current_phase, to_phase=phase, reason=reason,
            tick=tick))
        self.current_phase = phase
        self.phases_run.append(phase)

    def record_trace(self, phase: str, evidence: Dict[str, Any], *,
                     tick: int = 0) -> None:
        self.trace.append({"phase": phase, "tick": tick,
                           "evidence": dict(evidence)})

    def record_failure(self, phase: str, reason: str, *, tick: int = 0) -> None:
        self.failures.append(SoakPhaseFailure(phase=phase, reason=reason,
                                              tick=tick))

    def run_full_cycle(self, *, tick: int = 0,
                       phase_fn=None) -> List[str]:
        """Walk every bounded phase once, recording trace + failures.

        ``phase_fn(phase, tick) -> evidence dict`` performs the work of one
        phase; if it raises, the failure is recorded and the cycle continues to
        the next phase (failures are never hidden).
        """
        ran: List[str] = []
        for i, phase in enumerate(SoakRunPhase.ORDER):
            reason = "boot" if i == 0 else f"after {SoakRunPhase.ORDER[i - 1]}"
            self.enter(phase, reason, tick=tick)
            evidence: Dict[str, Any] = {"ran": True}
            if phase_fn is not None:
                try:
                    evidence = dict(phase_fn(phase, tick) or {"ran": True})
                except Exception as exc:
                    self.record_failure(phase, f"{type(exc).__name__}: {exc}",
                                        tick=tick)
                    evidence = {"ran": False, "failed": True}
            self.record_trace(phase, evidence, tick=tick)
            ran.append(phase)
        return ran

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_phase": self.current_phase,
            "phases_run": list(self.phases_run),
            "transition_count": len(self.transitions),
            "transitions": [t.to_dict() for t in self.transitions],
            "failure_count": len(self.failures),
            "failures": [f.to_dict() for f in self.failures],
            "trace_event_count": len(self.trace),
        }
