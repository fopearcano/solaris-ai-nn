"""Pilot-3 protocol -- gated phases for simulated/dry-run limited embodiment.

There is **no real-actuation phase**. The 24h plan is planning-only unless a
future explicit governance step extends it; the motor-firewall preflight must
pass before any sandbox action; and every phase shows
``real_world_authority = False``.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .safety import MotorMembraneSafetyValidator


class Pilot3Phase:
    PLAN_ONLY = "plan_only"
    MOTOR_FIREWALL_PREFLIGHT = "motor_firewall_preflight"
    DRY_RUN_MOTOR_TRACE = "dry_run_motor_trace"
    GRIDWORLD_SHORT = "gridworld_short"
    GRIDWORLD_REWARD_DANGER_SHORT = "gridworld_reward_danger_short"
    MIXED_SENSORY_GRIDWORLD_SHORT = "mixed_sensory_gridworld_short"
    LIMITED_EMBODIMENT_24H_PLAN = "limited_embodiment_24h_plan"
    POST_RUN_ANALYSIS = "post_run_analysis"

    ORDER = (PLAN_ONLY, MOTOR_FIREWALL_PREFLIGHT, DRY_RUN_MOTOR_TRACE,
             GRIDWORLD_SHORT, GRIDWORLD_REWARD_DANGER_SHORT,
             MIXED_SENSORY_GRIDWORLD_SHORT, LIMITED_EMBODIMENT_24H_PLAN,
             POST_RUN_ANALYSIS)
    ALL = ORDER
    # Phases that run sandbox actions (need a passing firewall preflight).
    SANDBOX = frozenset({GRIDWORLD_SHORT, GRIDWORLD_REWARD_DANGER_SHORT,
                         MIXED_SENSORY_GRIDWORLD_SHORT})


class Pilot3PhaseStatus:
    PENDING = "pending"
    ENTERED = "entered"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

    ALL = (PENDING, ENTERED, PASSED, FAILED, BLOCKED, SKIPPED)


@dataclass
class Pilot3PhaseRecord:
    phase: str
    status: str
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot3Protocol:
    """Drives and persists the gated Pilot-3 phases (no real actuation)."""

    base_dir: str = ".solaris_ai_nn_pilot3"
    pilot3_id: str = "PILOT3"
    safety: MotorMembraneSafetyValidator = field(
        default_factory=MotorMembraneSafetyValidator)
    current_phase: str = Pilot3Phase.PLAN_ONLY
    phase_status: Dict[str, str] = field(default_factory=dict)
    firewall_preflight_passed: bool = False
    real_world_authority: bool = False

    def __post_init__(self) -> None:
        if not self.phase_status:
            self.phase_status = {p: Pilot3PhaseStatus.PENDING
                                 for p in Pilot3Phase.ORDER}
        self.real_world_authority = False
        self._state_path = os.path.join(self.base_dir,
                                        "pilot3_protocol_state.json")
        self._history_path = os.path.join(self.base_dir,
                                          "pilot3_phase_history.jsonl")

    def entry_criteria(self, phase: str) -> List[str]:
        crit = ["motor safety validator active", "real_world_authority=false"]
        if phase in Pilot3Phase.SANDBOX:
            crit += ["motor firewall preflight passed"]
        return crit

    def exit_criteria(self, phase: str) -> List[str]:
        if phase == Pilot3Phase.MOTOR_FIREWALL_PREFLIGHT:
            return ["firewall always enabled", "real-world actions blocked"]
        if phase in Pilot3Phase.SANDBOX:
            return ["actions logged", "no real-world attempt executed",
                    "all results simulated"]
        return ["phase work completed"]

    def can_enter(self, phase: str) -> "tuple[bool, List[str]]":
        reasons: List[str] = []
        if phase not in Pilot3Phase.ORDER:
            return False, [f"unknown phase {phase!r}"]
        if phase in Pilot3Phase.SANDBOX and not self.firewall_preflight_passed:
            reasons.append("motor firewall preflight has not passed")
        return (not reasons), reasons

    def enter_phase(self, phase: str) -> Dict[str, Any]:
        ok, reasons = self.can_enter(phase)
        if not ok:
            self.phase_status[phase] = Pilot3PhaseStatus.BLOCKED
            self._record(phase, Pilot3PhaseStatus.BLOCKED, "; ".join(reasons))
            return {"entered": False, "phase": phase, "blocked": True,
                    "reasons": reasons}
        self.current_phase = phase
        self.phase_status[phase] = Pilot3PhaseStatus.ENTERED
        self._record(phase, Pilot3PhaseStatus.ENTERED, "entered")
        return {"entered": True, "phase": phase,
                "entry_criteria": self.entry_criteria(phase),
                "real_world_authority": False}

    def complete_phase(self, phase: str, passed: bool,
                       detail: str = "") -> Dict[str, Any]:
        status = Pilot3PhaseStatus.PASSED if passed \
            else Pilot3PhaseStatus.FAILED
        self.phase_status[phase] = status
        if passed and phase == Pilot3Phase.MOTOR_FIREWALL_PREFLIGHT:
            self.firewall_preflight_passed = True
        self._record(phase, status, detail)
        return {"phase": phase, "status": status,
                "real_world_authority": False}

    def _record(self, phase: str, status: str, detail: str) -> None:
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(Pilot3PhaseRecord(phase=phase, status=status,
                                                  detail=detail).to_dict(),
                                default=str) + "\n")
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(self.snapshot(), fh, indent=2, default=str)

    def snapshot(self) -> Dict[str, Any]:
        done = sum(1 for s in self.phase_status.values()
                   if s == Pilot3PhaseStatus.PASSED)
        return {
            "pilot3_id": self.pilot3_id,
            "current_phase": self.current_phase,
            "firewall_preflight_passed": self.firewall_preflight_passed,
            "real_world_authority": False,
            "has_real_actuation_phase": False,
            "phase_status": dict(self.phase_status),
            "completed_phases": done,
            "total_phases": len(Pilot3Phase.ORDER),
        }
