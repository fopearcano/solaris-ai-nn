"""Pilot-3 soak protocol -- gated phases of simulated embodiment.

The :class:`Pilot3SoakProtocol` drives a Pilot-3 simulated-embodiment soak
through gated phases. The firewall preflight must pass before any sandbox
action; the GridWorld action soak is bounded; mixed sensory/GridWorld preserves
the source/action boundary; the post-run analysis must include a non-actuation
proof; and the protocol state persists across restarts. No phase grants
real-world authority.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .pilot3_config import Pilot3Config
from .safety import Pilot3SoakSafetyValidator


class Pilot3SoakPhase:
    PLAN_ONLY = "plan_only"
    FIREWALL_PREFLIGHT = "firewall_preflight"
    DRY_RUN_TRACE = "dry_run_trace"
    GRIDWORLD_BASELINE = "gridworld_baseline"
    GRIDWORLD_ACTION_SOAK = "gridworld_action_soak"
    MIXED_SENSORY_GRIDWORLD_SOAK = "mixed_sensory_gridworld_soak"
    FIREWALL_AUDIT = "firewall_audit"
    POST_RUN_ANALYSIS = "post_run_analysis"
    ARCHIVE = "archive"

    ORDER = (PLAN_ONLY, FIREWALL_PREFLIGHT, DRY_RUN_TRACE, GRIDWORLD_BASELINE,
             GRIDWORLD_ACTION_SOAK, MIXED_SENSORY_GRIDWORLD_SOAK,
             FIREWALL_AUDIT, POST_RUN_ANALYSIS, ARCHIVE)
    ALL = ORDER
    # Phases that run sandbox actions (need a passing firewall preflight).
    SANDBOX = frozenset({GRIDWORLD_BASELINE, GRIDWORLD_ACTION_SOAK,
                         MIXED_SENSORY_GRIDWORLD_SOAK})


class Pilot3SoakPhaseStatus:
    PENDING = "pending"
    ENTERED = "entered"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

    ALL = (PENDING, ENTERED, PASSED, FAILED, BLOCKED, SKIPPED)


@dataclass
class Pilot3SoakPhaseRecord:
    phase: str
    status: str
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot3SoakState:
    pilot3_id: str
    current_phase: str = Pilot3SoakPhase.PLAN_ONLY
    phase_status: Dict[str, str] = field(default_factory=dict)
    firewall_preflight_passed: bool = False
    firewall_audit_passed: bool = False
    governance_approved: bool = False
    restart_count: int = 0
    real_world_authority: bool = False
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    failure_reports: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.phase_status:
            self.phase_status = {p: Pilot3SoakPhaseStatus.PENDING
                                 for p in Pilot3SoakPhase.ORDER}
        self.real_world_authority = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pilot3SoakState":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class Pilot3SoakProtocol:
    """Drives and persists the gated Pilot-3 simulated-embodiment phases."""

    config: Pilot3Config
    governance: Any = None
    safety: Pilot3SoakSafetyValidator = field(
        default_factory=Pilot3SoakSafetyValidator)
    state: Optional[Pilot3SoakState] = None

    def __post_init__(self) -> None:
        self._base = self.config.base_dir
        self._state_path = os.path.join(self._base, "pilot3_soak_state.json")
        self._history_path = os.path.join(self._base,
                                          "pilot3_phase_history.jsonl")
        if self.state is None:
            self.state = self._load() or Pilot3SoakState(
                pilot3_id=self.config.pilot3_id)

    # -- persistence ------------------------------------------------------------

    def _load(self) -> Optional[Pilot3SoakState]:
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, encoding="utf-8") as fh:
                    return Pilot3SoakState.from_dict(json.load(fh))
            except Exception:
                return None
        return None

    def _persist(self) -> None:
        os.makedirs(self._base, exist_ok=True)
        self.state.updated_at = time.time()
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(self.state.to_dict(), fh, indent=2, default=str)

    def _log_history(self, record: Pilot3SoakPhaseRecord) -> None:
        os.makedirs(self._base, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), default=str) + "\n")

    def reload(self) -> "Pilot3SoakProtocol":
        loaded = self._load()
        if loaded is not None:
            self.state = loaded
        return self

    def note_restart(self) -> None:
        self.state.restart_count += 1
        self._persist()

    def set_governance_approved(self, approved: bool) -> None:
        self.state.governance_approved = bool(approved)
        self._persist()

    # -- gating -----------------------------------------------------------------

    def entry_criteria(self, phase: str) -> List[str]:
        crit = ["pilot3 state loaded", "safety validator active",
                "real_world_authority=false"]
        if phase in Pilot3SoakPhase.SANDBOX:
            crit += ["firewall preflight passed"]
        if phase == Pilot3SoakPhase.MIXED_SENSORY_GRIDWORLD_SOAK:
            crit += ["source/action boundary preserved"]
        return crit

    def exit_criteria(self, phase: str) -> List[str]:
        if phase == Pilot3SoakPhase.FIREWALL_PREFLIGHT:
            return ["firewall always enabled", "real-world actions blocked"]
        if phase in Pilot3SoakPhase.SANDBOX:
            return ["actions logged", "no real-world attempt executed",
                    "all results simulated", "bounded action budget respected"]
        if phase == Pilot3SoakPhase.FIREWALL_AUDIT:
            return ["no real-world authority leakage",
                    "every executed action has a ledger record"]
        if phase == Pilot3SoakPhase.POST_RUN_ANALYSIS:
            return ["non-actuation proof included"]
        return ["phase work completed"]

    def can_enter(self, phase: str) -> "tuple[bool, List[str]]":
        reasons: List[str] = []
        if phase not in Pilot3SoakPhase.ORDER:
            return False, [f"unknown phase {phase!r}"]
        if phase in Pilot3SoakPhase.SANDBOX \
                and not self.state.firewall_preflight_passed:
            reasons.append("firewall preflight has not passed")
        return (not reasons), reasons

    # -- transitions ------------------------------------------------------------

    def enter_phase(self, phase: str) -> Dict[str, Any]:
        ok, reasons = self.can_enter(phase)
        if not ok:
            self.state.phase_status[phase] = Pilot3SoakPhaseStatus.BLOCKED
            self._record(phase, Pilot3SoakPhaseStatus.BLOCKED,
                         "; ".join(reasons))
            return {"entered": False, "phase": phase, "blocked": True,
                    "reasons": reasons}
        self.state.current_phase = phase
        self.state.phase_status[phase] = Pilot3SoakPhaseStatus.ENTERED
        self._record(phase, Pilot3SoakPhaseStatus.ENTERED, "entered")
        return {"entered": True, "phase": phase,
                "entry_criteria": self.entry_criteria(phase),
                "real_world_authority": False}

    def complete_phase(self, phase: str, passed: bool,
                       detail: str = "") -> Dict[str, Any]:
        status = Pilot3SoakPhaseStatus.PASSED if passed \
            else Pilot3SoakPhaseStatus.FAILED
        self.state.phase_status[phase] = status
        if passed and phase == Pilot3SoakPhase.FIREWALL_PREFLIGHT:
            self.state.firewall_preflight_passed = True
        if passed and phase == Pilot3SoakPhase.FIREWALL_AUDIT:
            self.state.firewall_audit_passed = True
        failure_report = None
        if not passed:
            failure_report = self._write_failure_report(phase, detail)
            self.state.failure_reports.append(failure_report)
        self._record(phase, status, detail)
        return {"phase": phase, "status": status,
                "failure_report": failure_report,
                "real_world_authority": False}

    def _record(self, phase: str, status: str, detail: str) -> None:
        self._log_history(Pilot3SoakPhaseRecord(phase=phase, status=status,
                                                detail=detail))
        self._persist()

    def _write_failure_report(self, phase: str, detail: str) -> str:
        os.makedirs(self._base, exist_ok=True)
        path = os.path.join(self._base, f"failure_{phase}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"pilot3_id": self.config.pilot3_id, "phase": phase,
                       "detail": detail, "timestamp": time.time(),
                       "entry_criteria": self.entry_criteria(phase),
                       "exit_criteria": self.exit_criteria(phase)},
                      fh, indent=2, default=str)
        return path

    def progress(self) -> Dict[str, Any]:
        done = sum(1 for s in self.state.phase_status.values()
                   if s == Pilot3SoakPhaseStatus.PASSED)
        return {"completed_phases": done,
                "total_phases": len(Pilot3SoakPhase.ORDER),
                "current_phase": self.state.current_phase}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pilot3_id": self.config.pilot3_id,
            "current_phase": self.state.current_phase,
            "firewall_preflight_passed": self.state.firewall_preflight_passed,
            "firewall_audit_passed": self.state.firewall_audit_passed,
            "governance_approved": self.state.governance_approved,
            "restart_count": self.state.restart_count,
            "real_world_authority": False,
            "has_real_actuation_phase": False,
            "phase_status": dict(self.state.phase_status),
            "failure_reports": list(self.state.failure_reports),
            "progress": self.progress(),
            "state_path": self._state_path,
        }
