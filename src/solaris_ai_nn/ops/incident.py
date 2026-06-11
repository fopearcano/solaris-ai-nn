"""Incidents -- the append-only record of operational trouble.

Every notable operational event (health warnings, watchdog shutdowns, gaps,
failures) becomes an Incident row in a JSONL log, with severity, the metric
that triggered it, and a suggested debug step. Evidence first, fixes never.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

HEALTH_WARNING = "health_warning"
HEALTH_CRITICAL = "health_critical"
WATCHDOG_SHUTDOWN = "watchdog_shutdown"
UNEXPECTED_DEATH = "unexpected_death_detected"
BRAIN_DEATH_GAP = "brain_death_gap"
CHECKPOINT_FAILURE = "checkpoint_failure"
ROTATION_FAILURE = "artifact_rotation_failure"
REPLAY_MISMATCH = "replay_mismatch"
PLASTICITY_VIOLATION = "plasticity_safety_violation"
EMBODIMENT_STUCK = "embodiment_stuck"
SUBSTRATE_RUNAWAY = "substrate_runaway"
SUBSTRATE_INERT = "substrate_inert"
BUDGET_VIOLATION = "budget_violation"
EMERGENCY_STOP = "emergency_stop"
POLICY_VIOLATION = "policy_violation"
LATENT_CYCLE_STUCK = "latent_cycle_stuck"
DREAM_TRACE_OVERGROWTH = "dream_trace_overgrowth"
COUNTERFACTUAL_LEAK = "counterfactual_leak"
LATENT_POLICY_VIOLATION = "latent_policy_violation"
MYSTERIUM_RUNAWAY = "mysterium_runaway"
HOMEOSTASIS_STUCK = "homeostasis_stuck"
RUNAWAY_NEED_PRESSURE = "runaway_need_pressure"
REPEATED_SUPPRESSED_DESIRES = "repeated_suppressed_desires"
AUTO_DETERMINATION_SHUTDOWN_RECOMMENDED = (
    "auto_determination_shutdown_recommended")
EXECUTIVE_NO_SAFE_ACTION = "executive_no_safe_action"
EXECUTIVE_REPEATED_INHIBITION = "executive_repeated_inhibition"
EXECUTIVE_PLAN_REJECTED = "executive_plan_rejected"
EXECUTIVE_PROSPECTION_FAILURE = "executive_prospection_failure"
EXECUTIVE_MODE_FORCED_EMERGENCY = "executive_mode_forced_emergency"

INCIDENT_TYPES = frozenset({
    HEALTH_WARNING, HEALTH_CRITICAL, WATCHDOG_SHUTDOWN, UNEXPECTED_DEATH,
    BRAIN_DEATH_GAP, CHECKPOINT_FAILURE, ROTATION_FAILURE, REPLAY_MISMATCH,
    PLASTICITY_VIOLATION, EMBODIMENT_STUCK, SUBSTRATE_RUNAWAY, SUBSTRATE_INERT,
    BUDGET_VIOLATION, EMERGENCY_STOP, POLICY_VIOLATION,
    LATENT_CYCLE_STUCK, DREAM_TRACE_OVERGROWTH, COUNTERFACTUAL_LEAK,
    LATENT_POLICY_VIOLATION, MYSTERIUM_RUNAWAY,
    HOMEOSTASIS_STUCK, RUNAWAY_NEED_PRESSURE, REPEATED_SUPPRESSED_DESIRES,
    AUTO_DETERMINATION_SHUTDOWN_RECOMMENDED,
    EXECUTIVE_NO_SAFE_ACTION, EXECUTIVE_REPEATED_INHIBITION,
    EXECUTIVE_PLAN_REJECTED, EXECUTIVE_PROSPECTION_FAILURE,
    EXECUTIVE_MODE_FORCED_EMERGENCY,
})

SEVERITIES = ("info", "warning", "critical")


@dataclass
class Incident:
    """One operational event worth remembering."""

    type: str
    severity: str
    message: str
    run_id: str = ""
    session_id: str = ""
    related_metric: Optional[str] = None
    suggested_debug_step: str = ""
    resolved: bool = False
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.type not in INCIDENT_TYPES:
            raise ValueError(f"unknown incident type {self.type!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"unknown severity {self.severity!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class IncidentLog:
    """Append-only JSONL incident store (survives restarts)."""

    path: Union[str, Path]
    run_id: str = ""
    session_id: str = ""
    _writer: Any = field(default=None, repr=False, init=False)

    def __post_init__(self) -> None:
        from ..runtime.persistence import JsonlWriter  # local: avoid cycles

        self.path = Path(self.path)
        self._writer = JsonlWriter(self.path, append=True)

    def record(self, type: str, severity: str, message: str,
               related_metric: Optional[str] = None,
               suggested_debug_step: str = "") -> Incident:
        incident = Incident(
            type=type, severity=severity, message=message,
            run_id=self.run_id, session_id=self.session_id,
            related_metric=related_metric,
            suggested_debug_step=suggested_debug_step)
        self._writer.write(incident.to_dict())
        return incident

    def list_incidents(self) -> List[Dict[str, Any]]:
        from ..runtime.persistence import read_jsonl

        if not Path(self.path).exists():
            return []
        return list(read_jsonl(self.path))

    def count_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for row in self.list_incidents():
            counts[row["type"]] = counts.get(row["type"], 0) + 1
        return counts

    def unresolved_count(self) -> int:
        return sum(1 for row in self.list_incidents() if not row.get("resolved"))

    def last(self) -> Optional[Dict[str, Any]]:
        rows = self.list_incidents()
        return rows[-1] if rows else None

    def close(self) -> None:
        self._writer.close()
