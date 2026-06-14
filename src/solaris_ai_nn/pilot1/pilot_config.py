"""Pilot-1 configuration -- the bounded, authority-scoped pilot setup.

A :class:`PilotConfig` pins everything a Pilot-1 window needs: its mode
(plan-only by default), its authority (always internal/simulation/read-only/
observe -- never real-world), its directories, its cadences, and its resource
budgets. Real-time modes are never labelled as simulated and vice versa; a
multi-month real run requires explicit governance approval; nothing here
starts a run.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_PILOT_DIR = ".solaris_ai_nn_pilot1"


class PilotMode:
    PLAN_ONLY = "plan_only"
    DRY_RUN_SIMULATED = "dry_run_simulated"
    TWENTY_FOUR_HOUR_REAL = "twenty_four_hour_real"
    SEVEN_DAY_REAL = "seven_day_real"
    THIRTY_DAY_REAL = "thirty_day_real"
    MULTI_MONTH_REAL = "multi_month_real"

    ALL = (PLAN_ONLY, DRY_RUN_SIMULATED, TWENTY_FOUR_HOUR_REAL,
           SEVEN_DAY_REAL, THIRTY_DAY_REAL, MULTI_MONTH_REAL)
    # Real-time modes that consume wall-clock time.
    REAL_TIME = frozenset({TWENTY_FOUR_HOUR_REAL, SEVEN_DAY_REAL,
                           THIRTY_DAY_REAL, MULTI_MONTH_REAL})
    # Modes that require explicit governance approval before a real run.
    APPROVAL_REQUIRED = frozenset({TWENTY_FOUR_HOUR_REAL, SEVEN_DAY_REAL,
                                   THIRTY_DAY_REAL, MULTI_MONTH_REAL})
    SIMULATED = frozenset({PLAN_ONLY, DRY_RUN_SIMULATED})
    # Approximate target duration in days per mode (for planning).
    TARGET_DAYS = {
        PLAN_ONLY: 0.0,
        DRY_RUN_SIMULATED: 30.0,
        TWENTY_FOUR_HOUR_REAL: 1.0,
        SEVEN_DAY_REAL: 7.0,
        THIRTY_DAY_REAL: 30.0,
        MULTI_MONTH_REAL: 90.0,
    }
    # Governance scope required to actually run each real mode.
    REQUIRED_SCOPE = {
        TWENTY_FOUR_HOUR_REAL: "enable_pilot1_24h_real",
        SEVEN_DAY_REAL: "enable_pilot1_7d_real",
        THIRTY_DAY_REAL: "enable_pilot1_30d_real",
        MULTI_MONTH_REAL: "enable_pilot1_multi_month_real",
    }


class PilotAuthority:
    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    READ_ONLY_STREAM = "read_only_stream"
    SIDECAR_OBSERVE_ONLY = "sidecar_observe_only"
    OPERATOR_SUPERVISED = "operator_supervised"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, READ_ONLY_STREAM,
           SIDECAR_OBSERVE_ONLY, OPERATOR_SUPERVISED)
    # Every authority here is internal-facing; real-world actuation is never
    # an option.
    RUNNABLE = frozenset(ALL)


@dataclass
class PilotEnvironment:
    """The on-disk layout of a pilot, all under one approved base directory."""

    base_dir: str = DEFAULT_PILOT_DIR
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    log_dir: Optional[str] = None
    report_dir: Optional[str] = None

    def __post_init__(self) -> None:
        base = self.base_dir
        self.state_dir = self.state_dir or os.path.join(base, "state")
        self.artifact_dir = self.artifact_dir or os.path.join(base,
                                                              "artifacts")
        self.log_dir = self.log_dir or os.path.join(base, "logs")
        self.report_dir = self.report_dir or os.path.join(base, "reports")

    def all_dirs(self) -> List[str]:
        return [self.base_dir, self.state_dir, self.artifact_dir,
                self.log_dir, self.report_dir]

    def ensure(self) -> "PilotEnvironment":
        for d in self.all_dirs():
            os.makedirs(d, exist_ok=True)
        return self

    def is_inside(self, path: str) -> bool:
        """Is ``path`` confined to the approved pilot base directory?"""
        try:
            base = os.path.abspath(self.base_dir)
            return os.path.commonpath([os.path.abspath(path), base]) == base
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PilotConfig:
    """The bounded, authority-scoped configuration of one Pilot-1 window."""

    pilot_id: str = field(default_factory=lambda: f"PILOT1_{uuid.uuid4().hex[:10]}")
    mode: str = PilotMode.PLAN_ONLY
    authority: str = PilotAuthority.SIMULATION_ONLY
    base_dir: str = DEFAULT_PILOT_DIR
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    log_dir: Optional[str] = None
    report_dir: Optional[str] = None
    seed: int = 7
    start_time: float = field(default_factory=time.time)
    target_duration_days: Optional[float] = None
    checkpoint_interval_minutes: float = 30.0
    health_check_interval_minutes: float = 15.0
    daily_report_hour: int = 0
    weekly_report_day: int = 6  # Sunday
    max_disk_mb: float = 2048.0
    max_memory_mb: float = 1024.0
    max_cpu_percent_hint: Optional[float] = None
    enable_developmental_runtime: bool = True
    enable_nursery: bool = True
    enable_proto_language: bool = True
    enable_active_perception: bool = True
    enable_hypothesis_engine: bool = True
    enable_logos: bool = True
    enable_autoregeneration: bool = True
    enable_llm_adapter: bool = False
    emergency_contact_note: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in PilotMode.ALL:
            raise ValueError(f"unknown pilot mode {self.mode!r}")
        if self.authority not in PilotAuthority.ALL:
            raise ValueError(f"unknown pilot authority {self.authority!r}")
        env = PilotEnvironment(
            base_dir=self.base_dir, state_dir=self.state_dir,
            artifact_dir=self.artifact_dir, log_dir=self.log_dir,
            report_dir=self.report_dir)
        self.state_dir = env.state_dir
        self.artifact_dir = env.artifact_dir
        self.log_dir = env.log_dir
        self.report_dir = env.report_dir
        if self.target_duration_days is None:
            self.target_duration_days = PilotMode.TARGET_DAYS.get(self.mode,
                                                                  0.0)
        # LLM adapter is never runtime authority and is off unless asked.
        self.enable_llm_adapter = bool(self.enable_llm_adapter)

    # -- derived properties ----------------------------------------------------

    @property
    def is_real_time(self) -> bool:
        return self.mode in PilotMode.REAL_TIME

    @property
    def is_simulated(self) -> bool:
        return self.mode in PilotMode.SIMULATED

    @property
    def requires_governance(self) -> bool:
        return self.mode in PilotMode.APPROVAL_REQUIRED

    @property
    def required_scope(self) -> Optional[str]:
        return PilotMode.REQUIRED_SCOPE.get(self.mode)

    @property
    def time_label(self) -> str:
        """A human label that never confuses simulated time with real time."""
        if self.is_simulated:
            return "SIMULATED-TIME (not a real month)"
        return "REAL-TIME (wall-clock)"

    def environment(self) -> PilotEnvironment:
        return PilotEnvironment(
            base_dir=self.base_dir, state_dir=self.state_dir,
            artifact_dir=self.artifact_dir, log_dir=self.log_dir,
            report_dir=self.report_dir)

    def enabled_modules(self) -> List[str]:
        """The conscience module names this pilot would enable."""
        mods = ["bridge", "ecology", "memory", "homeostasis", "executive",
                "governance", "ops", "world_model", "inner_map", "evaluation",
                "communication"]
        flag = {
            "developmental": self.enable_developmental_runtime,
            "ecology": self.enable_nursery,
            "protolanguage": self.enable_proto_language,
            "active_perception": self.enable_active_perception,
            "hypothesis": self.enable_hypothesis_engine,
            "logos": self.enable_logos,
            "autoregeneration": self.enable_autoregeneration,
            "llm_adapter": self.enable_llm_adapter,
        }
        for name, on in flag.items():
            if on and name not in mods:
                mods.append(name)
        return mods

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_real_time": self.is_real_time,
                "is_simulated": self.is_simulated,
                "requires_governance": self.requires_governance,
                "required_scope": self.required_scope,
                "time_label": self.time_label}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PilotConfig":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
