"""Pilot-2 configuration -- read-only environmental exposure, one-way.

A :class:`Pilot2Config` pins a Pilot-2 window: its mode (plan-only by
default), its authority (internal/simulation/read-only-environmental/operator-
supervised -- never real-world actuation), and its source mode (fixtures,
nursery, sensory-membrane, or mixed). Provenance is required by default; real
read-only environmental modes need approved input roots; and mixed mode
preserves the nursery/environment boundary.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_PILOT2_DIR = ".solaris_ai_nn_pilot2"


class Pilot2Mode:
    PLAN_ONLY = "plan_only"
    DRY_RUN = "dry_run"
    FIXTURE_SHORT = "fixture_short"
    NURSERY_BASELINE = "nursery_baseline"
    MIXED_SHORT = "mixed_short"
    READ_ONLY_24H = "read_only_24h"
    READ_ONLY_7D = "read_only_7d"
    READ_ONLY_30D = "read_only_30d"

    ALL = (PLAN_ONLY, DRY_RUN, FIXTURE_SHORT, NURSERY_BASELINE, MIXED_SHORT,
           READ_ONLY_24H, READ_ONLY_7D, READ_ONLY_30D)
    # Real read-only soak modes require governance approval.
    APPROVAL_REQUIRED = frozenset({READ_ONLY_24H, READ_ONLY_7D, READ_ONLY_30D})
    REAL_TIME = APPROVAL_REQUIRED
    FIXTURE_OR_PLAN = frozenset({PLAN_ONLY, DRY_RUN, FIXTURE_SHORT,
                                NURSERY_BASELINE, MIXED_SHORT})
    TARGET_DAYS = {READ_ONLY_24H: 1.0, READ_ONLY_7D: 7.0, READ_ONLY_30D: 30.0}
    REQUIRED_SCOPE = {
        READ_ONLY_24H: "enable_pilot2_real_read_only_24h",
        READ_ONLY_7D: "enable_pilot2_real_read_only_7d",
        READ_ONLY_30D: "enable_pilot2_real_read_only_30d",
    }


class Pilot2Authority:
    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    READ_ONLY_ENVIRONMENTAL = "read_only_environmental"
    OPERATOR_SUPERVISED = "operator_supervised"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, READ_ONLY_ENVIRONMENTAL,
           OPERATOR_SUPERVISED)
    RUNNABLE = frozenset(ALL)


class Pilot2SourceMode:
    FIXTURES_ONLY = "fixtures_only"
    NURSERY_ONLY = "nursery_only"
    SENSORY_MEMBRANE_ONLY = "sensory_membrane_only"
    MIXED_NURSERY_AND_MEMBRANE = "mixed_nursery_and_membrane"

    ALL = (FIXTURES_ONLY, NURSERY_ONLY, SENSORY_MEMBRANE_ONLY,
           MIXED_NURSERY_AND_MEMBRANE)


@dataclass
class Pilot2Config:
    """The bounded, read-only configuration of one Pilot-2 window."""

    pilot2_id: str = field(
        default_factory=lambda: f"PILOT2_{uuid.uuid4().hex[:10]}")
    mode: str = Pilot2Mode.PLAN_ONLY
    authority: str = Pilot2Authority.SIMULATION_ONLY
    source_mode: str = Pilot2SourceMode.FIXTURES_ONLY
    base_dir: str = DEFAULT_PILOT2_DIR
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    input_roots: List[str] = field(default_factory=list)
    report_dir: Optional[str] = None
    seed: int = 7
    target_duration_days: Optional[float] = None
    max_steps: Optional[int] = 80
    max_duration_s: Optional[float] = 600.0
    source_poll_interval_s: float = 5.0
    max_events_per_poll: int = 100
    max_events_per_day: int = 100000
    provenance_required: bool = True
    enable_nursery: bool = True
    enable_sensory_membrane: bool = True
    enable_proto_language: bool = True
    enable_active_perception: bool = True
    enable_hypothesis_engine: bool = True
    enable_logos: bool = True
    enable_autoregeneration: bool = True
    enable_comparison: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.mode not in Pilot2Mode.ALL:
            raise ValueError(f"unknown pilot2 mode {self.mode!r}")
        if self.authority not in Pilot2Authority.ALL:
            raise ValueError(f"unknown pilot2 authority {self.authority!r}")
        if self.source_mode not in Pilot2SourceMode.ALL:
            raise ValueError(f"unknown pilot2 source mode {self.source_mode!r}")
        base = self.base_dir
        self.state_dir = self.state_dir or os.path.join(base, "state")
        self.artifact_dir = self.artifact_dir or os.path.join(base,
                                                              "artifacts")
        self.report_dir = self.report_dir or os.path.join(base, "reports")
        if self.target_duration_days is None:
            self.target_duration_days = Pilot2Mode.TARGET_DAYS.get(self.mode,
                                                                   0.0)
        # Provenance is required by default; never silently turned off.
        self.provenance_required = bool(self.provenance_required)

    # -- derived properties ----------------------------------------------------

    @property
    def is_real_time(self) -> bool:
        return self.mode in Pilot2Mode.REAL_TIME

    @property
    def is_fixture_or_plan(self) -> bool:
        return self.mode in Pilot2Mode.FIXTURE_OR_PLAN

    @property
    def requires_governance(self) -> bool:
        return self.mode in Pilot2Mode.APPROVAL_REQUIRED

    @property
    def required_scope(self) -> Optional[str]:
        return Pilot2Mode.REQUIRED_SCOPE.get(self.mode)

    @property
    def uses_membrane(self) -> bool:
        return self.source_mode in (Pilot2SourceMode.SENSORY_MEMBRANE_ONLY,
                                    Pilot2SourceMode.MIXED_NURSERY_AND_MEMBRANE)

    @property
    def uses_nursery(self) -> bool:
        return self.source_mode in (Pilot2SourceMode.NURSERY_ONLY,
                                    Pilot2SourceMode.MIXED_NURSERY_AND_MEMBRANE)

    @property
    def time_label(self) -> str:
        if self.is_real_time:
            return "REAL-TIME read-only (wall-clock)"
        return "SIMULATED/FIXTURE (not a real soak)"

    def all_dirs(self) -> List[str]:
        return [self.base_dir, self.state_dir, self.artifact_dir,
                self.report_dir]

    def ensure_dirs(self) -> "Pilot2Config":
        for d in self.all_dirs():
            os.makedirs(d, exist_ok=True)
        return self

    def root_approved(self, path: str) -> bool:
        try:
            ap = os.path.abspath(path)
            return any(os.path.commonpath([ap, os.path.abspath(r)])
                       == os.path.abspath(r) for r in self.input_roots)
        except ValueError:
            return False

    def enabled_modules(self) -> List[str]:
        mods = ["bridge", "memory", "homeostasis", "executive", "governance",
                "ops", "world_model", "inner_map", "evaluation",
                "communication"]
        flags = {
            "ecology": self.enable_nursery,
            "sensory_membrane": self.enable_sensory_membrane,
            "protolanguage": self.enable_proto_language,
            "active_perception": self.enable_active_perception,
            "hypothesis": self.enable_hypothesis_engine,
            "logos": self.enable_logos,
            "autoregeneration": self.enable_autoregeneration,
            "developmental": True,
        }
        for name, on in flags.items():
            if on and name not in mods:
                mods.append(name)
        return mods

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_real_time": self.is_real_time,
                "requires_governance": self.requires_governance,
                "required_scope": self.required_scope,
                "uses_membrane": self.uses_membrane,
                "uses_nursery": self.uses_nursery,
                "time_label": self.time_label}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pilot2Config":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
