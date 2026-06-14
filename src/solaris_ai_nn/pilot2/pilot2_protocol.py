"""Pilot-2 protocol -- the gated phases of read-only environmental exposure.

The :class:`Pilot2Protocol` drives a Pilot-2 through gated phases, each with
entry/exit criteria. Real read-only soak phases require governance approval and
a passing source preflight; the 24h/7d/30d phases never start automatically;
and the protocol state persists across restarts.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .pilot2_config import Pilot2Config
from .safety import Pilot2SafetyValidator


class Pilot2Phase:
    PLAN_ONLY = "plan_only"
    SOURCE_PREFLIGHT = "source_preflight"
    MEMBRANE_DRY_RUN = "membrane_dry_run"
    FIXTURE_SHORT_RUN = "fixture_short_run"
    NURSERY_BASELINE_RUN = "nursery_baseline_run"
    MIXED_NURSERY_MEMBRANE_RUN = "mixed_nursery_membrane_run"
    READ_ONLY_24H_SOAK = "read_only_24h_soak"
    READ_ONLY_7D_SOAK = "read_only_7d_soak"
    READ_ONLY_30D_SOAK = "read_only_30d_soak"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    POST_RUN_ARCHIVE = "post_run_archive"

    ORDER = (PLAN_ONLY, SOURCE_PREFLIGHT, MEMBRANE_DRY_RUN, FIXTURE_SHORT_RUN,
             NURSERY_BASELINE_RUN, MIXED_NURSERY_MEMBRANE_RUN,
             READ_ONLY_24H_SOAK, READ_ONLY_7D_SOAK, READ_ONLY_30D_SOAK,
             COMPARATIVE_ANALYSIS, POST_RUN_ARCHIVE)
    ALL = ORDER
    REAL_SOAK = frozenset({READ_ONLY_24H_SOAK, READ_ONLY_7D_SOAK,
                           READ_ONLY_30D_SOAK})
    REQUIRED_SCOPE = {
        READ_ONLY_24H_SOAK: "enable_pilot2_real_read_only_24h",
        READ_ONLY_7D_SOAK: "enable_pilot2_real_read_only_7d",
        READ_ONLY_30D_SOAK: "enable_pilot2_real_read_only_30d",
    }


class Pilot2PhaseStatus:
    PENDING = "pending"
    ENTERED = "entered"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

    ALL = (PENDING, ENTERED, PASSED, FAILED, BLOCKED, SKIPPED)


@dataclass
class Pilot2PhaseRecord:
    phase: str
    status: str
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot2ProtocolState:
    pilot2_id: str
    current_phase: str = Pilot2Phase.PLAN_ONLY
    phase_status: Dict[str, str] = field(default_factory=dict)
    preflight_passed: bool = False
    membrane_dry_run_passed: bool = False
    governance_approved: bool = False
    restart_count: int = 0
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    failure_reports: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.phase_status:
            self.phase_status = {p: Pilot2PhaseStatus.PENDING
                                 for p in Pilot2Phase.ORDER}

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pilot2ProtocolState":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class Pilot2Protocol:
    """Drives and persists the gated Pilot-2 phases."""

    config: Pilot2Config
    governance: Any = None
    safety: Pilot2SafetyValidator = field(default_factory=Pilot2SafetyValidator)
    state: Optional[Pilot2ProtocolState] = None

    def __post_init__(self) -> None:
        self._base = self.config.base_dir
        self._state_path = os.path.join(self._base,
                                        "pilot2_protocol_state.json")
        self._history_path = os.path.join(self._base,
                                          "pilot2_phase_history.jsonl")
        if self.state is None:
            self.state = self._load() or Pilot2ProtocolState(
                pilot2_id=self.config.pilot2_id)

    # -- persistence ------------------------------------------------------------

    def _load(self) -> Optional[Pilot2ProtocolState]:
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, encoding="utf-8") as fh:
                    return Pilot2ProtocolState.from_dict(json.load(fh))
            except Exception:
                return None
        return None

    def _persist(self) -> None:
        os.makedirs(self._base, exist_ok=True)
        self.state.updated_at = time.time()
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(self.state.to_dict(), fh, indent=2, default=str)

    def _log_history(self, record: Pilot2PhaseRecord) -> None:
        os.makedirs(self._base, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), default=str) + "\n")

    def reload(self) -> "Pilot2Protocol":
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

    def _phase_governance_ok(self, phase: str) -> bool:
        if phase not in Pilot2Phase.REAL_SOAK:
            return True
        if self.state.governance_approved:
            return True
        scope = Pilot2Phase.REQUIRED_SCOPE.get(phase)
        if self.governance is not None and scope:
            try:
                return bool(self.governance.is_enabled(scope))
            except Exception:
                return False
        return False

    def entry_criteria(self, phase: str) -> List[str]:
        crit = ["pilot2 state loaded", "safety validator active"]
        if phase in Pilot2Phase.REAL_SOAK:
            crit += ["source preflight passed", "membrane dry-run passed",
                     f"governance approved for {phase}"]
        elif phase == Pilot2Phase.MIXED_NURSERY_MEMBRANE_RUN:
            crit += ["membrane dry-run passed"]
        elif phase not in (Pilot2Phase.PLAN_ONLY,
                           Pilot2Phase.SOURCE_PREFLIGHT):
            crit += ["source preflight passed"]
        return crit

    def exit_criteria(self, phase: str) -> List[str]:
        if phase == Pilot2Phase.SOURCE_PREFLIGHT:
            return ["all source checks ran", "read-only contracts valid"]
        if phase in Pilot2Phase.REAL_SOAK:
            return ["target duration reached or operator stop",
                    "provenance complete", "no unsafe source active",
                    "sensory input never became a command"]
        return ["phase work completed", "reports written"]

    def can_enter(self, phase: str) -> "tuple[bool, List[str]]":
        reasons: List[str] = []
        if phase not in Pilot2Phase.ORDER:
            return False, [f"unknown phase {phase!r}"]
        needs_preflight = phase not in (Pilot2Phase.PLAN_ONLY,
                                        Pilot2Phase.SOURCE_PREFLIGHT)
        if needs_preflight and not self.state.preflight_passed:
            reasons.append("source preflight has not passed")
        if phase == Pilot2Phase.MIXED_NURSERY_MEMBRANE_RUN \
                and not self.state.membrane_dry_run_passed:
            reasons.append("membrane dry-run has not passed")
        if phase in Pilot2Phase.REAL_SOAK \
                and not self.state.membrane_dry_run_passed:
            reasons.append("membrane dry-run has not passed")
        if not self._phase_governance_ok(phase):
            reasons.append(f"{phase} requires governance approval")
        return (not reasons), reasons

    # -- transitions ------------------------------------------------------------

    def enter_phase(self, phase: str) -> Dict[str, Any]:
        ok, reasons = self.can_enter(phase)
        if not ok:
            self.state.phase_status[phase] = Pilot2PhaseStatus.BLOCKED
            self._record(phase, Pilot2PhaseStatus.BLOCKED, "; ".join(reasons))
            return {"entered": False, "phase": phase, "blocked": True,
                    "reasons": reasons}
        self.state.current_phase = phase
        self.state.phase_status[phase] = Pilot2PhaseStatus.ENTERED
        self._record(phase, Pilot2PhaseStatus.ENTERED, "entered")
        return {"entered": True, "phase": phase,
                "entry_criteria": self.entry_criteria(phase)}

    def complete_phase(self, phase: str, passed: bool,
                       detail: str = "") -> Dict[str, Any]:
        status = Pilot2PhaseStatus.PASSED if passed \
            else Pilot2PhaseStatus.FAILED
        self.state.phase_status[phase] = status
        if passed and phase == Pilot2Phase.SOURCE_PREFLIGHT:
            self.state.preflight_passed = True
        if passed and phase == Pilot2Phase.MEMBRANE_DRY_RUN:
            self.state.membrane_dry_run_passed = True
        failure_report = None
        if not passed:
            failure_report = self._write_failure_report(phase, detail)
            self.state.failure_reports.append(failure_report)
        self._record(phase, status, detail)
        return {"phase": phase, "status": status,
                "failure_report": failure_report}

    def _record(self, phase: str, status: str, detail: str) -> None:
        self._log_history(Pilot2PhaseRecord(phase=phase, status=status,
                                            detail=detail))
        self._persist()

    def _write_failure_report(self, phase: str, detail: str) -> str:
        os.makedirs(self._base, exist_ok=True)
        path = os.path.join(self._base, f"failure_{phase}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"pilot2_id": self.config.pilot2_id, "phase": phase,
                       "detail": detail, "timestamp": time.time(),
                       "entry_criteria": self.entry_criteria(phase),
                       "exit_criteria": self.exit_criteria(phase)},
                      fh, indent=2, default=str)
        return path

    def progress(self) -> Dict[str, Any]:
        done = sum(1 for s in self.state.phase_status.values()
                   if s == Pilot2PhaseStatus.PASSED)
        return {"completed_phases": done, "total_phases": len(Pilot2Phase.ORDER),
                "current_phase": self.state.current_phase}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pilot2_id": self.config.pilot2_id,
            "current_phase": self.state.current_phase,
            "preflight_passed": self.state.preflight_passed,
            "membrane_dry_run_passed": self.state.membrane_dry_run_passed,
            "governance_approved": self.state.governance_approved,
            "restart_count": self.state.restart_count,
            "phase_status": dict(self.state.phase_status),
            "failure_reports": list(self.state.failure_reports),
            "progress": self.progress(),
            "state_path": self._state_path,
        }
