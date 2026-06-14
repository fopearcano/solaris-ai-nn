"""Pilot-1 protocol -- the ordered, gated phases of a long-horizon test.

The :class:`PilotProtocol` drives a pilot through explicit phases, each with
entry and exit criteria. The 30-day run cannot start until preflight passes
and governance approves; a failed phase produces a failure report; and the
whole protocol state persists across restarts so a multi-week pilot can be
resumed and audited.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .pilot_config import PilotConfig, PilotMode
from .safety import PilotSafetyValidator


class PilotPhase:
    PREFLIGHT = "preflight"
    BASELINE_SHORT_RUN = "baseline_short_run"
    RESTART_DRILL = "restart_drill"
    SIMULATED_MONTH_DRY_RUN = "simulated_month_dry_run"
    REAL_TIME_24H_SOAK = "real_time_24h_soak"
    REAL_TIME_7D_SOAK = "real_time_7d_soak"
    REAL_TIME_30D_SOAK = "real_time_30d_soak"
    POST_RUN_CONSOLIDATION = "post_run_consolidation"
    POST_RUN_ANALYSIS = "post_run_analysis"
    ARCHIVE = "archive"

    ORDER = (PREFLIGHT, BASELINE_SHORT_RUN, RESTART_DRILL,
             SIMULATED_MONTH_DRY_RUN, REAL_TIME_24H_SOAK, REAL_TIME_7D_SOAK,
             REAL_TIME_30D_SOAK, POST_RUN_CONSOLIDATION, POST_RUN_ANALYSIS,
             ARCHIVE)
    ALL = ORDER
    # Real-time soak phases that consume wall-clock time and need approval.
    REAL_TIME = frozenset({REAL_TIME_24H_SOAK, REAL_TIME_7D_SOAK,
                           REAL_TIME_30D_SOAK})
    REQUIRED_SCOPE = {
        REAL_TIME_24H_SOAK: "enable_pilot1_24h_real",
        REAL_TIME_7D_SOAK: "enable_pilot1_7d_real",
        REAL_TIME_30D_SOAK: "enable_pilot1_30d_real",
    }


class PilotPhaseStatus:
    PENDING = "pending"
    ENTERED = "entered"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

    ALL = (PENDING, ENTERED, PASSED, FAILED, BLOCKED, SKIPPED)


@dataclass
class PilotPhaseRecord:
    """One logged phase transition."""

    phase: str
    status: str
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PilotProtocolState:
    """The persistent state of a pilot protocol run."""

    pilot_id: str
    current_phase: str = PilotPhase.PREFLIGHT
    phase_status: Dict[str, str] = field(default_factory=dict)
    preflight_passed: bool = False
    governance_approved: bool = False
    restart_count: int = field(default=0)
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    failure_reports: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.phase_status:
            self.phase_status = {p: PilotPhaseStatus.PENDING
                                 for p in PilotPhase.ORDER}

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PilotProtocolState":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class PilotProtocol:
    """Drives and persists the gated Pilot-1 phases."""

    config: PilotConfig
    governance: Any = None
    safety: PilotSafetyValidator = field(default_factory=PilotSafetyValidator)
    state: Optional[PilotProtocolState] = None

    def __post_init__(self) -> None:
        self._base = self.config.base_dir
        self._state_path = os.path.join(self._base, "pilot_protocol_state.json")
        self._history_path = os.path.join(self._base,
                                          "pilot_phase_history.jsonl")
        if self.state is None:
            self.state = self._load() or PilotProtocolState(
                pilot_id=self.config.pilot_id)

    # -- persistence ------------------------------------------------------------

    def _load(self) -> Optional[PilotProtocolState]:
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, encoding="utf-8") as fh:
                    return PilotProtocolState.from_dict(json.load(fh))
            except Exception:
                return None
        return None

    def _persist(self) -> None:
        os.makedirs(self._base, exist_ok=True)
        self.state.updated_at = time.time()
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(self.state.to_dict(), fh, indent=2, default=str)

    def _log_history(self, record: PilotPhaseRecord) -> None:
        os.makedirs(self._base, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), default=str) + "\n")

    def reload(self) -> "PilotProtocol":
        """Re-read state from disk (e.g. after a restart)."""
        loaded = self._load()
        if loaded is not None:
            self.state = loaded
        return self

    def note_restart(self) -> None:
        self.state.restart_count += 1
        self._persist()

    # -- approval ---------------------------------------------------------------

    def set_governance_approved(self, approved: bool) -> None:
        self.state.governance_approved = bool(approved)
        self._persist()

    def _phase_governance_ok(self, phase: str) -> bool:
        if phase not in PilotPhase.REAL_TIME:
            return True
        if self.state.governance_approved:
            return True
        scope = PilotPhase.REQUIRED_SCOPE.get(phase)
        if self.governance is not None and scope:
            try:
                return bool(self.governance.is_enabled(scope))
            except Exception:
                return False
        return False

    # -- entry / exit criteria --------------------------------------------------

    def entry_criteria(self, phase: str) -> List[str]:
        crit = ["pilot state is loaded", "safety validator is active"]
        if phase == PilotPhase.REAL_TIME_30D_SOAK:
            crit += ["preflight passed", "governance approved for 30d real",
                     "restart drill passed", "simulated dry-run reviewed"]
        elif phase in PilotPhase.REAL_TIME:
            crit += ["preflight passed", f"governance approved for {phase}"]
        elif phase == PilotPhase.SIMULATED_MONTH_DRY_RUN:
            crit += ["clearly labelled simulated", "preflight passed"]
        elif phase != PilotPhase.PREFLIGHT:
            crit += ["preflight passed"]
        return crit

    def exit_criteria(self, phase: str) -> List[str]:
        if phase == PilotPhase.PREFLIGHT:
            return ["health check ran", "safety check passed",
                    "governance check ran", "directories validated"]
        if phase in PilotPhase.REAL_TIME:
            return ["target duration reached or operator stop",
                    "checkpoints intact", "observability complete",
                    "no unresolved critical safety incident"]
        return ["phase work completed", "reports written"]

    def can_enter(self, phase: str) -> "tuple[bool, List[str]]":
        """Whether ``phase`` may be entered; returns (ok, blocking reasons)."""
        reasons: List[str] = []
        if phase not in PilotPhase.ORDER:
            return False, [f"unknown phase {phase!r}"]
        if phase != PilotPhase.PREFLIGHT and not self.state.preflight_passed:
            reasons.append("preflight has not passed")
        if not self._phase_governance_ok(phase):
            reasons.append(f"{phase} requires governance approval")
        return (not reasons), reasons

    # -- transitions ------------------------------------------------------------

    def enter_phase(self, phase: str) -> Dict[str, Any]:
        ok, reasons = self.can_enter(phase)
        if not ok:
            self.state.phase_status[phase] = PilotPhaseStatus.BLOCKED
            self._record(phase, PilotPhaseStatus.BLOCKED, "; ".join(reasons))
            return {"entered": False, "phase": phase, "blocked": True,
                    "reasons": reasons}
        self.state.current_phase = phase
        self.state.phase_status[phase] = PilotPhaseStatus.ENTERED
        self._record(phase, PilotPhaseStatus.ENTERED, "entered")
        return {"entered": True, "phase": phase,
                "entry_criteria": self.entry_criteria(phase)}

    def complete_phase(self, phase: str, passed: bool,
                       detail: str = "") -> Dict[str, Any]:
        status = PilotPhaseStatus.PASSED if passed else PilotPhaseStatus.FAILED
        self.state.phase_status[phase] = status
        if phase == PilotPhase.PREFLIGHT and passed:
            self.state.preflight_passed = True
        failure_report = None
        if not passed:
            failure_report = self._write_failure_report(phase, detail)
            self.state.failure_reports.append(failure_report)
        self._record(phase, status, detail)
        return {"phase": phase, "status": status,
                "failure_report": failure_report}

    def _record(self, phase: str, status: str, detail: str) -> None:
        self._log_history(PilotPhaseRecord(phase=phase, status=status,
                                           detail=detail))
        self._persist()

    def _write_failure_report(self, phase: str, detail: str) -> str:
        os.makedirs(self._base, exist_ok=True)
        path = os.path.join(self._base, f"failure_{phase}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"pilot_id": self.config.pilot_id, "phase": phase,
                       "detail": detail, "timestamp": time.time(),
                       "entry_criteria": self.entry_criteria(phase),
                       "exit_criteria": self.exit_criteria(phase)},
                      fh, indent=2, default=str)
        return path

    # -- views ------------------------------------------------------------------

    def progress(self) -> Dict[str, Any]:
        done = sum(1 for s in self.state.phase_status.values()
                   if s == PilotPhaseStatus.PASSED)
        return {"completed_phases": done, "total_phases": len(PilotPhase.ORDER),
                "current_phase": self.state.current_phase}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pilot_id": self.config.pilot_id,
            "current_phase": self.state.current_phase,
            "preflight_passed": self.state.preflight_passed,
            "governance_approved": self.state.governance_approved,
            "restart_count": self.state.restart_count,
            "phase_status": dict(self.state.phase_status),
            "failure_reports": list(self.state.failure_reports),
            "progress": self.progress(),
            "state_path": self._state_path,
            "history_path": self._history_path,
        }
