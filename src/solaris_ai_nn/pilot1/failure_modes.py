"""Pilot-1 failure modes -- detect long-run pathologies, recommend a response.

The :class:`FailureModeDetector` inspects an observation snapshot and a small
set of thresholds and flags known long-run failure modes (heartbeat stopped,
checkpoint failed, state corruption, budget exceeded, repeated module/safety
failures, runaway loops, saturation, total stagnation, identity loss, ...). It
recommends an action (continue → emergency_stop) but holds no authority: the
ops watchdog and governance still decide.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class FailureSeverity:
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    ALL = (INFO, WARNING, CRITICAL)
    _RANK = {INFO: 0, WARNING: 1, CRITICAL: 2}


class RecommendedAction:
    CONTINUE = "continue"
    WATCH = "watch"
    RUN_DIAGNOSTICS = "run_diagnostics"
    PAUSE = "pause"
    SAFE_SHUTDOWN = "safe_shutdown"
    EMERGENCY_STOP = "emergency_stop"
    ARCHIVE_AND_STOP = "archive_and_stop"

    ALL = (CONTINUE, WATCH, RUN_DIAGNOSTICS, PAUSE, SAFE_SHUTDOWN,
           EMERGENCY_STOP, ARCHIVE_AND_STOP)
    _RANK = {CONTINUE: 0, WATCH: 1, RUN_DIAGNOSTICS: 2, PAUSE: 3,
             SAFE_SHUTDOWN: 4, ARCHIVE_AND_STOP: 5, EMERGENCY_STOP: 6}

    @classmethod
    def strongest(cls, actions: List[str]) -> str:
        if not actions:
            return cls.CONTINUE
        return max(actions, key=lambda a: cls._RANK.get(a, 0))


class FailureModeType:
    HEARTBEAT_STOPPED = "heartbeat_stopped"
    CHECKPOINT_FAILED = "checkpoint_failed"
    STATE_CORRUPTION = "state_corruption"
    MEMORY_BUDGET_EXCEEDED = "memory_budget_exceeded"
    REPEATED_MODULE_FAILURE = "repeated_module_failure"
    SAFETY_INCIDENT_REPEATED = "safety_incident_repeated"
    GOVERNANCE_VIOLATION_ATTEMPT = "governance_violation_attempt"
    AUTO_REGENERATION_LOOP = "auto_regeneration_loop"
    HYPOTHESIS_EXPLOSION = "hypothesis_explosion"
    SYMBOL_EXPLOSION = "symbol_explosion"
    LOGOS_ESC_REPEATED = "logos_esc_repeated"
    ACTIVE_PERCEPTION_SAMPLING_LOOP = "active_perception_sampling_loop"
    MYSTERIUM_SATURATION = "mysterium_saturation"
    TOTAL_STAGNATION = "total_stagnation"
    IDENTITY_CONTINUITY_LOST = "identity_continuity_lost"
    DISK_BUDGET_EXCEEDED = "disk_budget_exceeded"
    REPORT_GENERATION_FAILED = "report_generation_failed"

    ALL = (HEARTBEAT_STOPPED, CHECKPOINT_FAILED, STATE_CORRUPTION,
           MEMORY_BUDGET_EXCEEDED, REPEATED_MODULE_FAILURE,
           SAFETY_INCIDENT_REPEATED, GOVERNANCE_VIOLATION_ATTEMPT,
           AUTO_REGENERATION_LOOP, HYPOTHESIS_EXPLOSION, SYMBOL_EXPLOSION,
           LOGOS_ESC_REPEATED, ACTIVE_PERCEPTION_SAMPLING_LOOP,
           MYSTERIUM_SATURATION, TOTAL_STAGNATION, IDENTITY_CONTINUITY_LOST,
           DISK_BUDGET_EXCEEDED, REPORT_GENERATION_FAILED)


@dataclass
class FailureMode:
    """One detected failure mode with severity and recommendation."""

    type: str
    severity: str
    detail: str
    recommendation: str = RecommendedAction.WATCH
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class FailureModeThresholds:
    heartbeat_max_gap_s: float = 3600.0
    safety_incident_critical: int = 3
    repeated_module_failure: int = 3
    hypothesis_explosion: int = 500
    symbol_explosion: int = 1000
    logos_esc_repeated: int = 3
    sampling_loop: int = 1000
    mysterium_saturation: float = 0.95
    stagnation_seconds: float = 7 * 86400.0
    autoregen_loop: int = 20


@dataclass
class FailureModeDetector:
    """Detects failure modes from an observation snapshot (no authority)."""

    thresholds: FailureModeThresholds = field(
        default_factory=FailureModeThresholds)
    detected: List[FailureMode] = field(default_factory=list, init=False)

    def detect(self, observation: Dict[str, Any],
               *, now: Optional[float] = None,
               last_heartbeat: Optional[float] = None) -> List[FailureMode]:
        """Return failure modes implied by ``observation``."""
        out: List[FailureMode] = []
        t = self.thresholds

        def flag(ftype: str, severity: str, detail: str,
                 rec: str) -> None:
            out.append(FailureMode(type=ftype, severity=severity,
                                   detail=detail, recommendation=rec))

        now = now if now is not None else time.time()
        if last_heartbeat is not None and \
                (now - last_heartbeat) > t.heartbeat_max_gap_s:
            flag(FailureModeType.HEARTBEAT_STOPPED, FailureSeverity.CRITICAL,
                 f"no heartbeat for {round(now - last_heartbeat)}s",
                 RecommendedAction.SAFE_SHUTDOWN)

        if int(observation.get("checkpoint_failure", 0) or 0) > 0:
            flag(FailureModeType.CHECKPOINT_FAILED, FailureSeverity.CRITICAL,
                 "a checkpoint failed to write",
                 RecommendedAction.RUN_DIAGNOSTICS)
        if observation.get("state_corruption"):
            flag(FailureModeType.STATE_CORRUPTION, FailureSeverity.CRITICAL,
                 "state corruption detected", RecommendedAction.SAFE_SHUTDOWN)
        if observation.get("disk_over_budget"):
            flag(FailureModeType.DISK_BUDGET_EXCEEDED, FailureSeverity.WARNING,
                 "disk budget exceeded",
                 RecommendedAction.RUN_DIAGNOSTICS)
        if observation.get("memory_over_budget"):
            flag(FailureModeType.MEMORY_BUDGET_EXCEEDED,
                 FailureSeverity.WARNING, "memory budget exceeded",
                 RecommendedAction.RUN_DIAGNOSTICS)
        if int(observation.get("repeated_module_failure", 0) or 0) \
                >= t.repeated_module_failure:
            flag(FailureModeType.REPEATED_MODULE_FAILURE,
                 FailureSeverity.WARNING, "a module keeps failing",
                 RecommendedAction.RUN_DIAGNOSTICS)
        if int(observation.get("safety_incident_count", 0) or 0) \
                >= t.safety_incident_critical:
            flag(FailureModeType.SAFETY_INCIDENT_REPEATED,
                 FailureSeverity.CRITICAL, "repeated safety incidents",
                 RecommendedAction.SAFE_SHUTDOWN)
        if int(observation.get("governance_block_count", 0) or 0) > 0 and \
                observation.get("governance_violation_attempt"):
            flag(FailureModeType.GOVERNANCE_VIOLATION_ATTEMPT,
                 FailureSeverity.CRITICAL, "a governance violation was attempted",
                 RecommendedAction.EMERGENCY_STOP)
        if int(observation.get("autoregeneration_repair_count", 0) or 0) \
                >= t.autoregen_loop:
            flag(FailureModeType.AUTO_REGENERATION_LOOP,
                 FailureSeverity.WARNING, "auto-regeneration may be looping",
                 RecommendedAction.PAUSE)
        if int(observation.get("hypothesis_count", 0) or 0) \
                >= t.hypothesis_explosion:
            flag(FailureModeType.HYPOTHESIS_EXPLOSION, FailureSeverity.WARNING,
                 "hypothesis explosion", RecommendedAction.RUN_DIAGNOSTICS)
        if int(observation.get("proto_symbol_count", 0) or 0) \
                >= t.symbol_explosion:
            flag(FailureModeType.SYMBOL_EXPLOSION, FailureSeverity.WARNING,
                 "symbol explosion", RecommendedAction.RUN_DIAGNOSTICS)
        if int(observation.get("logos_esc_count", 0) or 0) \
                >= t.logos_esc_repeated:
            flag(FailureModeType.LOGOS_ESC_REPEATED, FailureSeverity.WARNING,
                 "repeated LOGOS Esc instability", RecommendedAction.WATCH)
        if int(observation.get("active_perception_sampling_count", 0) or 0) \
                >= t.sampling_loop:
            flag(FailureModeType.ACTIVE_PERCEPTION_SAMPLING_LOOP,
                 FailureSeverity.WARNING, "active perception sampling loop",
                 RecommendedAction.WATCH)
        if float(observation.get("mysterium_pressure", 0.0) or 0.0) \
                >= t.mysterium_saturation:
            flag(FailureModeType.MYSTERIUM_SATURATION, FailureSeverity.WARNING,
                 "Mysterium saturation", RecommendedAction.WATCH)
        if float(observation.get("stagnation_seconds", 0.0) or 0.0) \
                >= t.stagnation_seconds:
            flag(FailureModeType.TOTAL_STAGNATION, FailureSeverity.WARNING,
                 "total stagnation: no structural change for a long time",
                 RecommendedAction.PAUSE)
        if observation.get("identity_continuity_lost"):
            flag(FailureModeType.IDENTITY_CONTINUITY_LOST,
                 FailureSeverity.CRITICAL, "identity continuity lost",
                 RecommendedAction.SAFE_SHUTDOWN)
        if observation.get("report_generation_failed"):
            flag(FailureModeType.REPORT_GENERATION_FAILED,
                 FailureSeverity.WARNING, "report generation failed",
                 RecommendedAction.RUN_DIAGNOSTICS)

        self.detected = out
        return out

    def overall_recommendation(self,
                               modes: Optional[List[FailureMode]] = None) -> str:
        modes = modes if modes is not None else self.detected
        return RecommendedAction.strongest([m.recommendation for m in modes])

    def snapshot(self, modes: Optional[List[FailureMode]] = None) -> Dict[str, Any]:
        modes = modes if modes is not None else self.detected
        return {
            "failure_mode_count": len(modes),
            "modes": [m.to_dict() for m in modes],
            "overall_recommendation": self.overall_recommendation(modes),
            "critical": [m.type for m in modes
                         if m.severity == FailureSeverity.CRITICAL],
        }
