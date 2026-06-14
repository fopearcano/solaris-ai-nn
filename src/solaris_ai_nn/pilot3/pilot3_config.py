"""Pilot-3 configuration -- simulated embodiment soak, sandbox-only, one-way out.

A :class:`Pilot3Config` pins a Pilot-3 simulated-embodiment window: its mode
(plan-only by default), its authority (internal / simulation / dry-run /
sandbox -- never real-world), and its embodiment condition (no body, read-only
perception, GridWorld body, mixed sensory+GridWorld, or dry-run motor).
``real_world_authority`` is always false; any config that tries to claim it
fails validation; soak modes are simulation/sandbox-only and bounded.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_PILOT3_DIR = ".solaris_ai_nn_pilot3"


class Pilot3Mode:
    PLAN_ONLY = "plan_only"
    FIREWALL_PREFLIGHT = "firewall_preflight"
    DRY_RUN_MOTOR_TRACE = "dry_run_motor_trace"
    GRIDWORLD_SHORT = "gridworld_short"
    GRIDWORLD_SOAK_SIMULATED = "gridworld_soak_simulated"
    MIXED_SENSORY_GRIDWORLD_SHORT = "mixed_sensory_gridworld_short"
    MIXED_SENSORY_GRIDWORLD_SOAK = "mixed_sensory_gridworld_soak"
    COMPARATIVE_ANALYSIS = "comparative_analysis"

    ALL = (PLAN_ONLY, FIREWALL_PREFLIGHT, DRY_RUN_MOTOR_TRACE, GRIDWORLD_SHORT,
           GRIDWORLD_SOAK_SIMULATED, MIXED_SENSORY_GRIDWORLD_SHORT,
           MIXED_SENSORY_GRIDWORLD_SOAK, COMPARATIVE_ANALYSIS)
    # Bounded simulated soaks need an explicit bounded config (still no
    # real-world authority; see the policy gate).
    SOAK = frozenset({GRIDWORLD_SOAK_SIMULATED, MIXED_SENSORY_GRIDWORLD_SOAK})
    # Modes that run sandbox actions (need a passing firewall preflight).
    SANDBOX = frozenset({GRIDWORLD_SHORT, GRIDWORLD_SOAK_SIMULATED,
                         MIXED_SENSORY_GRIDWORLD_SHORT,
                         MIXED_SENSORY_GRIDWORLD_SOAK})
    MIXED = frozenset({MIXED_SENSORY_GRIDWORLD_SHORT,
                       MIXED_SENSORY_GRIDWORLD_SOAK})
    REQUIRED_SCOPE = {
        PLAN_ONLY: "enable_pilot3_soak",
        FIREWALL_PREFLIGHT: "enable_pilot3_firewall_preflight",
        DRY_RUN_MOTOR_TRACE: "enable_pilot3_dry_run_trace",
        GRIDWORLD_SHORT: "enable_pilot3_gridworld_short",
        GRIDWORLD_SOAK_SIMULATED: "enable_pilot3_gridworld_soak_simulated",
        MIXED_SENSORY_GRIDWORLD_SHORT: "enable_pilot3_mixed_sensory_gridworld",
        MIXED_SENSORY_GRIDWORLD_SOAK: "enable_pilot3_mixed_sensory_gridworld",
        COMPARATIVE_ANALYSIS: "enable_pilot3_post_analysis",
    }


class Pilot3Authority:
    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    DRY_RUN_ONLY = "dry_run_only"
    SANDBOX_ONLY = "sandbox_only"
    FORBIDDEN_REAL_WORLD = "forbidden_real_world"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, DRY_RUN_ONLY, SANDBOX_ONLY,
           FORBIDDEN_REAL_WORLD)
    # Authorities a Pilot-3 window may actually run under (never real-world).
    RUNNABLE = frozenset({INTERNAL_ONLY, SIMULATION_ONLY, DRY_RUN_ONLY,
                          SANDBOX_ONLY})


class EmbodimentCondition:
    NO_BODY = "no_body"
    READ_ONLY_PERCEPTION = "read_only_perception"
    GRIDWORLD_BODY = "gridworld_body"
    MIXED_SENSORY_GRIDWORLD = "mixed_sensory_gridworld"
    DRY_RUN_MOTOR = "dry_run_motor"

    ALL = (NO_BODY, READ_ONLY_PERCEPTION, GRIDWORLD_BODY,
           MIXED_SENSORY_GRIDWORLD, DRY_RUN_MOTOR)


@dataclass
class Pilot3Config:
    """The bounded, simulation-only configuration of one Pilot-3 window."""

    pilot3_id: str = field(
        default_factory=lambda: f"PILOT3_{uuid.uuid4().hex[:10]}")
    mode: str = Pilot3Mode.PLAN_ONLY
    authority: str = Pilot3Authority.SIMULATION_ONLY
    condition: str = EmbodimentCondition.NO_BODY
    base_dir: str = DEFAULT_PILOT3_DIR
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    sandbox_dir: Optional[str] = None
    report_dir: Optional[str] = None
    seed: int = 7
    max_steps: Optional[int] = 80
    max_duration_s: Optional[float] = 600.0
    target_duration_days_equivalent: float = 0.0
    simulated_time: bool = True
    time_acceleration: float = 1.0
    enable_gridworld: bool = True
    enable_sensory_membrane: bool = False
    enable_motor_membrane: bool = True
    enable_action_grounding: bool = True
    enable_firewall_audit: bool = True
    enable_comparative_analysis: bool = True
    max_actions_per_step: int = 1
    max_total_actions: int = 2000
    max_veto_rate_warning: float = 0.5
    real_world_authority: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.mode not in Pilot3Mode.ALL:
            raise ValueError(f"unknown pilot3 mode {self.mode!r}")
        if self.authority not in Pilot3Authority.ALL:
            raise ValueError(f"unknown pilot3 authority {self.authority!r}")
        if self.condition not in EmbodimentCondition.ALL:
            raise ValueError(f"unknown embodiment condition {self.condition!r}")
        # Hard invariant: a Pilot-3 window never has real-world authority.
        if self.real_world_authority or self.authority == \
                Pilot3Authority.FORBIDDEN_REAL_WORLD \
                or self.metadata.get("real_world_authority") \
                or self.metadata.get("real_world_actuation"):
            raise ValueError(
                "Pilot-3 can never have real-world authority/actuation; it is "
                "simulation/dry-run/sandbox only")
        if self.mode in Pilot3Mode.SOAK and self.authority not in \
                Pilot3Authority.RUNNABLE:
            raise ValueError("soak modes must be simulation/sandbox only")
        # Bounded by construction: soaks must carry a finite step/time bound.
        if self.mode in Pilot3Mode.SOAK and not (self.max_steps
                                                 or self.max_duration_s):
            raise ValueError("soak modes must be bounded (max_steps or "
                             "max_duration_s)")
        self.real_world_authority = False
        base = self.base_dir
        self.state_dir = self.state_dir or os.path.join(base, "state")
        self.artifact_dir = self.artifact_dir or os.path.join(base, "artifacts")
        self.sandbox_dir = self.sandbox_dir or os.path.join(base, "sandbox")
        self.report_dir = self.report_dir or os.path.join(base, "reports")

    # -- derived properties ----------------------------------------------------

    @property
    def is_soak(self) -> bool:
        return self.mode in Pilot3Mode.SOAK

    @property
    def is_sandbox_action_mode(self) -> bool:
        return self.mode in Pilot3Mode.SANDBOX

    @property
    def is_mixed(self) -> bool:
        return self.mode in Pilot3Mode.MIXED

    @property
    def is_dry_run(self) -> bool:
        return self.mode == Pilot3Mode.DRY_RUN_MOTOR_TRACE \
            or self.authority == Pilot3Authority.DRY_RUN_ONLY \
            or self.condition == EmbodimentCondition.DRY_RUN_MOTOR

    @property
    def required_scope(self) -> Optional[str]:
        return Pilot3Mode.REQUIRED_SCOPE.get(self.mode)

    @property
    def time_label(self) -> str:
        return "SIMULATED embodiment (sandbox; not real embodiment)"

    def all_dirs(self) -> List[str]:
        return [self.base_dir, self.state_dir, self.artifact_dir,
                self.sandbox_dir, self.report_dir]

    def ensure_dirs(self) -> "Pilot3Config":
        for d in self.all_dirs():
            os.makedirs(d, exist_ok=True)
        return self

    def sandbox_root_approved(self, path: str) -> bool:
        """True only when ``path`` is inside an approved state/artifact root."""
        roots = [self.state_dir, self.artifact_dir, self.sandbox_dir,
                 self.base_dir]
        try:
            ap = os.path.abspath(path)
            return any(os.path.commonpath([ap, os.path.abspath(r)])
                       == os.path.abspath(r) for r in roots if r)
        except ValueError:
            return False

    def enabled_modules(self) -> List[str]:
        mods = ["bridge", "memory", "homeostasis", "executive", "governance",
                "ops", "world_model", "inner_map", "evaluation",
                "communication"]
        flags = {
            "motor_membrane": self.enable_motor_membrane,
            "sensory_membrane": self.enable_sensory_membrane,
            "protolanguage": True,
            "active_perception": True,
            "hypothesis": True,
            "logos": True,
            "autoregeneration": True,
            "developmental": True,
        }
        for name, on in flags.items():
            if on and name not in mods:
                mods.append(name)
        return mods

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "is_soak": self.is_soak,
                "is_sandbox_action_mode": self.is_sandbox_action_mode,
                "is_mixed": self.is_mixed,
                "is_dry_run": self.is_dry_run,
                "required_scope": self.required_scope,
                "time_label": self.time_label}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pilot3Config":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
