"""OperationalRunManifest -- the contract for any supervised run.

Long-running modes are never the default and never silent: ``continuous_explicit``
requires ``explicit_continuous_acknowledged=True``, and the soak modes require
``soak_acknowledged=True``. Tests simulate durations; nothing here sleeps.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class RunMode:
    BOUNDED = "bounded"
    SOAK_24H = "soak_24h"
    SOAK_30D = "soak_30d"
    CONTINUOUS_EXPLICIT = "continuous_explicit"

    ALL = (BOUNDED, SOAK_24H, SOAK_30D, CONTINUOUS_EXPLICIT)
    SOAK_MODES = (SOAK_24H, SOAK_30D)


class RunSafetyMode:
    OBSERVE_ONLY = "observe_only"
    SIMULATION_ONLY = "simulation_only"
    SIDECAR_OBSERVE_ONLY = "sidecar_observe_only"
    BENCHMARK_ONLY = "benchmark_only"

    ALL = (OBSERVE_ONLY, SIMULATION_ONLY, SIDECAR_OBSERVE_ONLY, BENCHMARK_ONLY)


DEFAULT_OPS_FEATURES = {
    "plasticity": False, "embodiment": False, "language": False,
    "sidecar": False, "evaluation": False, "local_status_server": False,
}

SOAK_DURATIONS = {RunMode.SOAK_24H: 24 * 3600.0, RunMode.SOAK_30D: 30 * 24 * 3600.0}


@dataclass
class OperationalRunManifest:
    """Pins how a supervised run is allowed to behave."""

    mode: str = RunMode.BOUNDED
    safety_mode: str = RunSafetyMode.SIMULATION_ONLY
    state_dir: str = ".solaris_ai_nn_state/ops_run"
    artifact_dir: str = ".solaris_ai_nn_ops"
    max_steps: Optional[int] = 300
    max_duration_s: Optional[float] = None
    heartbeat_interval_s: float = 1.0
    checkpoint_interval_steps: int = 50
    healthcheck_interval_steps: int = 50
    watchdog_interval_s: float = 5.0
    substrate: str = "esn"
    enabled_features: Dict[str, bool] = field(
        default_factory=lambda: dict(DEFAULT_OPS_FEATURES))
    explicit_continuous_acknowledged: bool = False
    soak_acknowledged: bool = False
    operator_notes: str = ""
    seed: int = 7
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    expected_stop_time: Optional[float] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.mode not in RunMode.ALL:
            raise ValueError(f"unknown run mode {self.mode!r}")
        if self.safety_mode not in RunSafetyMode.ALL:
            raise ValueError(f"unknown safety mode {self.safety_mode!r}")
        if self.mode == RunMode.CONTINUOUS_EXPLICIT \
                and not self.explicit_continuous_acknowledged:
            raise ValueError(
                "continuous_explicit mode requires "
                "explicit_continuous_acknowledged=True -- continuity is never "
                "silent")
        if self.mode in RunMode.SOAK_MODES and not self.soak_acknowledged:
            raise ValueError(
                f"{self.mode} requires soak_acknowledged=True (long soaks are "
                "opt-in; test with short bounded runs first)")
        if self.mode in RunMode.SOAK_MODES and self.max_duration_s is None:
            self.max_duration_s = SOAK_DURATIONS[self.mode]
        if self.mode == RunMode.BOUNDED \
                and self.max_steps is None and self.max_duration_s is None:
            raise ValueError("bounded mode requires max_steps and/or "
                             "max_duration_s")
        if self.max_duration_s is not None:
            self.expected_stop_time = self.created_at + self.max_duration_s

    def is_bounded(self) -> bool:
        return self.max_steps is not None or self.max_duration_s is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id, "session_id": self.session_id,
            "created_at": self.created_at, "mode": self.mode,
            "safety_mode": self.safety_mode,
            "state_dir": self.state_dir, "artifact_dir": self.artifact_dir,
            "max_steps": self.max_steps, "max_duration_s": self.max_duration_s,
            "heartbeat_interval_s": self.heartbeat_interval_s,
            "checkpoint_interval_steps": self.checkpoint_interval_steps,
            "healthcheck_interval_steps": self.healthcheck_interval_steps,
            "watchdog_interval_s": self.watchdog_interval_s,
            "substrate": self.substrate,
            "enabled_features": dict(self.enabled_features),
            "explicit_continuous_acknowledged":
                self.explicit_continuous_acknowledged,
            "soak_acknowledged": self.soak_acknowledged,
            "expected_stop_time": self.expected_stop_time,
            "operator_notes": self.operator_notes,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationalRunManifest":
        valid = set(cls.__dataclass_fields__) - {"expected_stop_time"}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
