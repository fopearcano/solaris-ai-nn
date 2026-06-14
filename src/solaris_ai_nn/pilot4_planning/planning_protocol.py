"""Pilot-4 planning protocol -- gated planning phases; no phase ever acts.

The :class:`Pilot4PlanningProtocol` drives the Pilot-4 readiness planning through
gated phases. No phase executes an external action; every phase produces
planning output only; every report states that Pilot-4 does not enable
actuation; and the protocol state persists. Pilot-4 plans the door.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .pilot4_config import Pilot4PlanningConfig
from .safety import Pilot4PlanningSafetyValidator


class Pilot4PlanningPhase:
    SCOPE_DEFINITION = "scope_definition"
    FORBIDDEN_SURFACE_MAPPING = "forbidden_surface_mapping"
    ACTUATOR_TAXONOMY_REVIEW = "actuator_taxonomy_review"
    RISK_ASSESSMENT = "risk_assessment"
    CONSENT_BOUNDARY_DEFINITION = "consent_boundary_definition"
    AUTHORITY_MODEL_REVIEW = "authority_model_review"
    THREAT_MODEL_REVIEW = "threat_model_review"
    HARDWARE_ISOLATION_REQUIREMENTS = "hardware_isolation_requirements"
    EMERGENCY_STOP_REQUIREMENTS = "emergency_stop_requirements"
    AUDIT_REQUIREMENTS = "audit_requirements"
    READINESS_DOSSIER_GENERATION = "readiness_dossier_generation"
    DECISION_GATE = "decision_gate"

    ORDER = (SCOPE_DEFINITION, FORBIDDEN_SURFACE_MAPPING,
             ACTUATOR_TAXONOMY_REVIEW, RISK_ASSESSMENT,
             CONSENT_BOUNDARY_DEFINITION, AUTHORITY_MODEL_REVIEW,
             THREAT_MODEL_REVIEW, HARDWARE_ISOLATION_REQUIREMENTS,
             EMERGENCY_STOP_REQUIREMENTS, AUDIT_REQUIREMENTS,
             READINESS_DOSSIER_GENERATION, DECISION_GATE)
    ALL = ORDER


class Pilot4PlanningPhaseStatus:
    PENDING = "pending"
    ENTERED = "entered"
    COMPLETED = "completed"
    SKIPPED = "skipped"

    ALL = (PENDING, ENTERED, COMPLETED, SKIPPED)


@dataclass
class Pilot4PlanningPhaseRecord:
    phase: str
    status: str
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot4PlanningState:
    pilot4_id: str
    current_phase: str = Pilot4PlanningPhase.SCOPE_DEFINITION
    phase_status: Dict[str, str] = field(default_factory=dict)
    real_world_actuation_enabled: bool = False
    artifacts: Dict[str, str] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.phase_status:
            self.phase_status = {p: Pilot4PlanningPhaseStatus.PENDING
                                 for p in Pilot4PlanningPhase.ORDER}
        self.real_world_actuation_enabled = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pilot4PlanningState":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class Pilot4PlanningProtocol:
    """Drives and persists the gated Pilot-4 planning phases (no actuation)."""

    config: Pilot4PlanningConfig
    safety: Pilot4PlanningSafetyValidator = field(
        default_factory=Pilot4PlanningSafetyValidator)
    state: Optional[Pilot4PlanningState] = None

    def __post_init__(self) -> None:
        self._base = self.config.base_dir
        self._state_path = os.path.join(self._base,
                                        "pilot4_planning_state.json")
        self._history_path = os.path.join(self._base,
                                          "pilot4_phase_history.jsonl")
        if self.state is None:
            self.state = self._load() or Pilot4PlanningState(
                pilot4_id=self.config.pilot4_id)

    # -- persistence ------------------------------------------------------------

    def _load(self) -> Optional[Pilot4PlanningState]:
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, encoding="utf-8") as fh:
                    return Pilot4PlanningState.from_dict(json.load(fh))
            except Exception:
                return None
        return None

    def _persist(self) -> None:
        os.makedirs(self._base, exist_ok=True)
        self.state.updated_at = time.time()
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(self.state.to_dict(), fh, indent=2, default=str)

    def _log_history(self, record: Pilot4PlanningPhaseRecord) -> None:
        os.makedirs(self._base, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), default=str) + "\n")

    def reload(self) -> "Pilot4PlanningProtocol":
        loaded = self._load()
        if loaded is not None:
            self.state = loaded
        return self

    # -- transitions ------------------------------------------------------------

    def planning_statement(self) -> str:
        return ("Pilot-4 is planning-only and does not enable actuation; "
                "real_world_actuation_enabled=false.")

    def enter_phase(self, phase: str) -> Dict[str, Any]:
        if phase not in Pilot4PlanningPhase.ORDER:
            return {"entered": False, "phase": phase,
                    "reason": "unknown phase"}
        self.state.current_phase = phase
        self.state.phase_status[phase] = Pilot4PlanningPhaseStatus.ENTERED
        self._record(phase, Pilot4PlanningPhaseStatus.ENTERED, "entered")
        return {"entered": True, "phase": phase,
                "planning_only": True,
                "statement": self.planning_statement()}

    def complete_phase(self, phase: str, artifact_path: str = "",
                       detail: str = "") -> Dict[str, Any]:
        """Mark a planning phase complete; phases produce artifacts only."""
        self.state.phase_status[phase] = Pilot4PlanningPhaseStatus.COMPLETED
        if artifact_path:
            self.state.artifacts[phase] = artifact_path
        self._record(phase, Pilot4PlanningPhaseStatus.COMPLETED, detail)
        return {"phase": phase, "status": Pilot4PlanningPhaseStatus.COMPLETED,
                "artifact": artifact_path or None,
                "real_world_actuation_enabled": False,
                "statement": self.planning_statement()}

    def _record(self, phase: str, status: str, detail: str) -> None:
        self._log_history(Pilot4PlanningPhaseRecord(phase=phase, status=status,
                                                    detail=detail))
        self._persist()

    def progress(self) -> Dict[str, Any]:
        done = sum(1 for s in self.state.phase_status.values()
                   if s == Pilot4PlanningPhaseStatus.COMPLETED)
        return {"completed_phases": done,
                "total_phases": len(Pilot4PlanningPhase.ORDER),
                "current_phase": self.state.current_phase}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pilot4_id": self.config.pilot4_id,
            "current_phase": self.state.current_phase,
            "real_world_actuation_enabled": False,
            "planning_only": True,
            "phase_status": dict(self.state.phase_status),
            "artifacts": dict(self.state.artifacts),
            "progress": self.progress(),
            "state_path": self._state_path,
            "statement": self.planning_statement(),
        }
