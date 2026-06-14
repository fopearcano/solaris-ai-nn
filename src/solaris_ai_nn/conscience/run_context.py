"""Run context -- the bounded, authority-scoped configuration of one run.

A :class:`RunContext` pins everything a unified run needs: its mode, its
authority (always internal/simulation/read-only/observe -- never real-world),
its bounds, its directories, and which modules are enabled. Month/year *real*
modes require governance approval; the default is a short bounded simulated
run; and nothing runs unbounded by default.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RunMode:
    UNIT_TEST = "unit_test"
    SHORT_DEMO = "short_demo"
    DEVELOPMENTAL_SIMULATED = "developmental_simulated"
    NURSERY_SIMULATED = "nursery_simulated"
    MONTH_SCALE_PLAN = "month_scale_plan"
    MONTH_SCALE_REAL = "month_scale_real"
    YEAR_SCALE_PLAN = "year_scale_plan"
    YEAR_SCALE_REAL = "year_scale_real"
    SIDECAR_OBSERVE = "sidecar_observe"
    READ_ONLY_STREAM = "read_only_stream"
    EMERGENCY = "emergency"

    ALL = (UNIT_TEST, SHORT_DEMO, DEVELOPMENTAL_SIMULATED, NURSERY_SIMULATED,
           MONTH_SCALE_PLAN, MONTH_SCALE_REAL, YEAR_SCALE_PLAN,
           YEAR_SCALE_REAL, SIDECAR_OBSERVE, READ_ONLY_STREAM, EMERGENCY)
    # Modes that require explicit governance approval to run for real.
    APPROVAL_REQUIRED = frozenset({MONTH_SCALE_REAL, YEAR_SCALE_REAL})
    # Plan-only modes generate a plan and never start a long run.
    PLAN_ONLY = frozenset({MONTH_SCALE_PLAN, YEAR_SCALE_PLAN})


class RunAuthority:
    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    READ_ONLY = "read_only"
    SIDECAR_OBSERVE_ONLY = "sidecar_observe_only"
    OPERATOR_SUPERVISED = "operator_supervised"
    FORBIDDEN = "forbidden"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, READ_ONLY, SIDECAR_OBSERVE_ONLY,
           OPERATOR_SUPERVISED, FORBIDDEN)
    # Authorities a run may actually use (never real-world).
    RUNNABLE = frozenset({INTERNAL_ONLY, SIMULATION_ONLY, READ_ONLY,
                          SIDECAR_OBSERVE_ONLY, OPERATOR_SUPERVISED})


@dataclass
class RunBoundary:
    """The hard bounds a run cannot exceed."""

    max_steps: Optional[int] = 500
    max_duration_s: Optional[float] = 600.0
    target_runtime_days: Optional[float] = None

    @property
    def is_bounded(self) -> bool:
        return self.max_steps is not None or self.max_duration_s is not None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RunContext:
    """The bounded, authority-scoped configuration of one unified run."""

    mode: str = RunMode.SHORT_DEMO
    authority: str = RunAuthority.SIMULATION_ONLY
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    simulated_time: bool = True
    time_acceleration: float = 3600.0
    max_steps: Optional[int] = 200
    max_duration_s: Optional[float] = 600.0
    target_runtime_days: Optional[float] = None
    enabled_modules: List[str] = field(default_factory=list)
    disabled_modules: List[str] = field(default_factory=list)
    governance_profile: str = "default"
    safety_profile: str = "default"
    seed: int = 7
    run_id: str = field(default_factory=lambda: f"RUN_{uuid.uuid4().hex[:10]}")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in RunMode.ALL:
            raise ValueError(f"unknown run mode {self.mode!r}")
        if self.authority not in RunAuthority.ALL:
            raise ValueError(f"unknown run authority {self.authority!r}")

    @property
    def is_plan_only(self) -> bool:
        return self.mode in RunMode.PLAN_ONLY

    @property
    def requires_governance(self) -> bool:
        return self.mode in RunMode.APPROVAL_REQUIRED

    @property
    def is_bounded(self) -> bool:
        return (self.is_plan_only
                or self.max_steps is not None
                or self.max_duration_s is not None)

    def boundary(self) -> RunBoundary:
        return RunBoundary(max_steps=self.max_steps,
                           max_duration_s=self.max_duration_s,
                           target_runtime_days=self.target_runtime_days)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_plan_only": self.is_plan_only,
                "requires_governance": self.requires_governance,
                "is_bounded": self.is_bounded}
