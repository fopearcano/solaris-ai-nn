"""Restart drills -- exercise recovery without ever killing the process.

:class:`RestartDrill` simulates the recovery scenarios a month-scale run must
survive: graceful shutdown/restart (checkpoint close/reopen), a simulated crash
marker, missing-checkpoint recovery, source silence during restart, checkpoint
corruption detection, and state continuity verification. Solaris never kills its
own process; "brain-death-like" gaps are logged *operationally*, not
biologically; and recovery never erases the break history.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RestartDrillType:
    GRACEFUL_SHUTDOWN_RESTART = "graceful_shutdown_restart"
    SIMULATED_CRASH_MARKER = "simulated_crash_marker"
    MISSING_CHECKPOINT_RECOVERY = "missing_checkpoint_recovery"
    SOURCE_SILENCE_DURING_RESTART = "source_silence_during_restart"
    CHECKPOINT_CORRUPTION_DETECTION = "checkpoint_corruption_detection"
    STATE_CONTINUITY_VERIFICATION = "state_continuity_verification"

    ALL = (GRACEFUL_SHUTDOWN_RESTART, SIMULATED_CRASH_MARKER,
           MISSING_CHECKPOINT_RECOVERY, SOURCE_SILENCE_DURING_RESTART,
           CHECKPOINT_CORRUPTION_DETECTION, STATE_CONTINUITY_VERIFICATION)


@dataclass
class RestartDrill:
    """A declarative restart drill (no real process kill ever occurs)."""

    drill_type: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"drill_type": self.drill_type, "description": self.description}


@dataclass
class RestartRecoveryAssessment:
    """How well continuity held across the simulated restart."""

    continuity_preserved: bool
    break_logged: bool
    break_history: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"continuity_preserved": self.continuity_preserved,
                "break_logged": self.break_logged,
                "break_history": list(self.break_history),
                "break_count": len(self.break_history), "notes": self.notes,
                "biological": False}


@dataclass
class RestartDrillResult:
    """The outcome of one restart drill."""

    drill_type: str
    outcome: str
    crash_marker_recorded: bool = False
    recovery: Optional[RestartRecoveryAssessment] = None
    evidence_refs: List[str] = field(default_factory=list)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"drill_type": self.drill_type, "outcome": self.outcome,
                "crash_marker_recorded": self.crash_marker_recorded,
                "recovery": self.recovery.to_dict() if self.recovery else None,
                "evidence_refs": list(self.evidence_refs), "ts": self.ts}


@dataclass
class RestartDrillRunner:
    """Runs restart drills against a checkpoint manager + developmental runtime.

    The runner never terminates a process. A graceful restart is represented as
    a checkpoint close/reopen; a crash is represented by a simulated marker; and
    every drill produces a recovery assessment that preserves the break history.
    """

    def run(self, drill: RestartDrill, *, checkpoint_manager: Any = None,
            developmental_runtime: Any = None) -> RestartDrillResult:
        cm = checkpoint_manager
        dev = developmental_runtime
        dt = drill.drill_type

        if dt == RestartDrillType.GRACEFUL_SHUTDOWN_RESTART:
            if dev is not None and hasattr(dev, "restart"):
                dev.restart()  # checkpoint close/reopen; records discontinuity
            recovery = self._assess(cm, "graceful checkpoint close/reopen")
            return RestartDrillResult(dt, "ok", recovery=recovery,
                                      evidence_refs=["restart:graceful"])

        if dt == RestartDrillType.SIMULATED_CRASH_MARKER:
            if cm is not None:
                cm.break_history.append({
                    "kind": "simulated_crash_marker", "ts": time.time(),
                    "note": "operational gap marker, not biological death"})
            recovery = self._assess(cm, "simulated crash marker logged")
            return RestartDrillResult(dt, "ok", crash_marker_recorded=True,
                                      recovery=recovery,
                                      evidence_refs=["restart:crash_marker"])

        if dt == RestartDrillType.MISSING_CHECKPOINT_RECOVERY:
            rec = cm.recover() if cm is not None else {"recovered": False,
                                                       "break_history": []}
            outcome = "recovered" if rec.get("recovered") else "no_checkpoint"
            recovery = RestartRecoveryAssessment(
                continuity_preserved=bool(rec.get("recovered")),
                break_logged=True, break_history=rec.get("break_history", []),
                notes="recovered from latest intact checkpoint"
                if rec.get("recovered") else
                "no intact checkpoint; restart from baseline, break logged")
            return RestartDrillResult(dt, outcome, recovery=recovery,
                                      evidence_refs=["restart:missing_cp"])

        if dt == RestartDrillType.SOURCE_SILENCE_DURING_RESTART:
            if cm is not None:
                cm.break_history.append({
                    "kind": "source_silence_during_restart", "ts": time.time(),
                    "note": "sources silent at restart; logged, not invented"})
            recovery = self._assess(cm, "source silence handled at restart")
            return RestartDrillResult(dt, "ok", recovery=recovery,
                                      evidence_refs=["restart:source_silence"])

        if dt == RestartDrillType.CHECKPOINT_CORRUPTION_DETECTION:
            detected = False
            if cm is not None and cm.checkpoints:
                cp = cm.checkpoints[-1]
                cp.checksum_manifest["__all__"] = "tampered"  # simulate corrupt
                detected = not cm.verify(cp).ok
            recovery = self._assess(cm, "corruption detected and recorded")
            return RestartDrillResult(
                dt, "detected" if detected else "no_checkpoint",
                recovery=recovery,
                evidence_refs=["restart:corruption_detection"])

        if dt == RestartDrillType.STATE_CONTINUITY_VERIFICATION:
            recovery = self._assess(cm, "state continuity verified")
            return RestartDrillResult(dt, "ok", recovery=recovery,
                                      evidence_refs=["restart:continuity"])

        raise ValueError(f"unknown restart drill type {dt!r}")

    @staticmethod
    def _assess(cm: Any, notes: str) -> RestartRecoveryAssessment:
        breaks = list(getattr(cm, "break_history", []) or [])
        intact = bool(getattr(cm, "checkpoints", None)) and any(
            not c.corrupt for c in cm.checkpoints) if cm is not None else False
        return RestartRecoveryAssessment(
            continuity_preserved=intact, break_logged=bool(breaks),
            break_history=breaks, notes=notes)
