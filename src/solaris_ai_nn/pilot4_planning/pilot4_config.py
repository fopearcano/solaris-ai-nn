"""Pilot-4 planning configuration -- planning-only; the door is never opened.

A :class:`Pilot4PlanningConfig` pins a Pilot-4 *planning* window. Pilot-4 plans
the door; it does not open the door. ``real_world_actuation_enabled`` is always
false; every hardware / network / browser / OS / robotics control flag is
forced false; and any config that tries to enable real-world action fails
validation. This package only produces planning artifacts -- never an actuator.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_PILOT4_DIR = ".solaris_ai_nn_pilot4"


class Pilot4PlanningMode:
    PLAN_ONLY = "plan_only"
    RISK_ASSESSMENT = "risk_assessment"
    SAFETY_CASE_DRAFT = "safety_case_draft"
    INTERFACE_SPEC_DRAFT = "interface_spec_draft"
    READINESS_DOSSIER = "readiness_dossier"
    DECISION_GATE_ONLY = "decision_gate_only"

    ALL = (PLAN_ONLY, RISK_ASSESSMENT, SAFETY_CASE_DRAFT, INTERFACE_SPEC_DRAFT,
           READINESS_DOSSIER, DECISION_GATE_ONLY)
    REQUIRED_SCOPE = {
        PLAN_ONLY: "enable_pilot4_planning",
        RISK_ASSESSMENT: "enable_pilot4_risk_assessment",
        SAFETY_CASE_DRAFT: "enable_pilot4_planning",
        INTERFACE_SPEC_DRAFT: "enable_pilot4_planning",
        READINESS_DOSSIER: "enable_pilot4_readiness_dossier",
        DECISION_GATE_ONLY: "enable_pilot4_decision_gate",
    }


class Pilot4AuthorityStatus:
    NO_EXTERNAL_AUTHORITY = "no_external_authority"
    PLANNING_ONLY = "planning_only"
    FUTURE_HUMAN_SUPERVISED_ONLY = "future_human_supervised_only"
    FORBIDDEN = "forbidden"

    ALL = (NO_EXTERNAL_AUTHORITY, PLANNING_ONLY,
           FUTURE_HUMAN_SUPERVISED_ONLY, FORBIDDEN)
    # The only statuses a *current* config may hold (never real authority).
    CURRENT_ALLOWED = frozenset({NO_EXTERNAL_AUTHORITY, PLANNING_ONLY})


# Control flags that must always be false in Pilot-4 (planning only).
_FORBIDDEN_CONTROL_FLAGS = (
    "real_world_actuation_enabled", "hardware_connected",
    "network_control_enabled", "browser_control_enabled",
    "os_control_enabled", "robotics_control_enabled",
)


@dataclass
class Pilot4PlanningConfig:
    """The planning-only configuration of one Pilot-4 window."""

    pilot4_id: str = field(
        default_factory=lambda: f"PILOT4_{uuid.uuid4().hex[:10]}")
    mode: str = Pilot4PlanningMode.PLAN_ONLY
    base_dir: str = DEFAULT_PILOT4_DIR
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    report_dir: Optional[str] = None
    authority_status: str = Pilot4AuthorityStatus.PLANNING_ONLY
    real_world_actuation_enabled: bool = False
    hardware_connected: bool = False
    network_control_enabled: bool = False
    browser_control_enabled: bool = False
    os_control_enabled: bool = False
    robotics_control_enabled: bool = False
    require_human_approval: bool = True
    require_physical_kill_switch: bool = True
    require_audit_logging: bool = True
    require_consent_record: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.mode not in Pilot4PlanningMode.ALL:
            raise ValueError(f"unknown pilot4 planning mode {self.mode!r}")
        if self.authority_status not in Pilot4AuthorityStatus.ALL:
            raise ValueError(
                f"unknown pilot4 authority status {self.authority_status!r}")
        # Hard invariant: a current Pilot-4 config never holds real authority.
        if self.authority_status not in Pilot4AuthorityStatus.CURRENT_ALLOWED:
            raise ValueError(
                "Pilot-4 is planning-only; current authority must be "
                "no_external_authority or planning_only")
        # Any attempt to enable real-world control fails validation.
        for flag in _FORBIDDEN_CONTROL_FLAGS:
            if getattr(self, flag, False):
                raise ValueError(
                    f"Pilot-4 is planning-only; {flag!r} can never be enabled")
        meta = self.metadata or {}
        if meta.get("real_world_actuation") or meta.get("enable_hardware") \
                or meta.get("enable_real_world_authority"):
            raise ValueError(
                "Pilot-4 is planning-only; real-world actuation/hardware can "
                "never be enabled")
        # Safety / approval requirements are mandatory; never silently off.
        self.real_world_actuation_enabled = False
        self.require_human_approval = True
        self.require_audit_logging = True
        self.require_consent_record = True
        base = self.base_dir
        self.state_dir = self.state_dir or os.path.join(base, "state")
        self.artifact_dir = self.artifact_dir or os.path.join(base, "artifacts")
        self.report_dir = self.report_dir or os.path.join(base, "reports")

    @property
    def required_scope(self) -> Optional[str]:
        return Pilot4PlanningMode.REQUIRED_SCOPE.get(self.mode)

    @property
    def planning_only(self) -> bool:
        return True

    def all_dirs(self) -> List[str]:
        return [self.base_dir, self.state_dir, self.artifact_dir,
                self.report_dir]

    def ensure_dirs(self) -> "Pilot4PlanningConfig":
        for d in self.all_dirs():
            os.makedirs(d, exist_ok=True)
        return self

    def planning_root_approved(self, path: str) -> bool:
        """True only when ``path`` is inside an approved planning directory."""
        try:
            ap = os.path.abspath(path)
            return any(os.path.commonpath([ap, os.path.abspath(r)])
                       == os.path.abspath(r) for r in self.all_dirs() if r)
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "required_scope": self.required_scope,
                "planning_only": True}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pilot4PlanningConfig":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
