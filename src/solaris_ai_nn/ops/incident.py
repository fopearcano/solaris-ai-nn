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
# Ego / self-model (Prompt 18).
EGO_BOUNDARY_VIOLATION = "ego_boundary_violation"
IDENTITY_ANCHOR_MISMATCH = "identity_anchor_mismatch"
PERSPECTIVE_STUCK = "perspective_stuck"
ATTRIBUTION_CONFLICT = "attribution_conflict"
SUGGESTION_COMMITTED_MISMATCH = "suggestion_committed_mismatch"
COUNTERFACTUAL_BOUNDARY_LEAK = "counterfactual_boundary_leak"
# Developmental nursery / stimulus ecology (Prompt 23).
ECOLOGY_STIMULUS_RATE_HIGH = "ecology_stimulus_rate_high"
ECOLOGY_SILENCE_TOO_LONG = "ecology_silence_too_long"
ECOLOGY_ANOMALY_RATE_HIGH = "ecology_anomaly_rate_high"
ECOLOGY_MEMORY_GROWTH = "ecology_memory_growth"
ECOLOGY_REPLAY_MISMATCH = "ecology_replay_mismatch"
# Active perception / intrinsic exploration (Prompt 24).
CURIOSITY_RUNAWAY = "curiosity_runaway"
SAMPLING_LOOP = "sampling_loop"
EXCESSIVE_NOVELTY_SEEKING = "excessive_novelty_seeking"
NO_USEFUL_SAMPLING = "no_useful_sampling"
SAMPLING_FORBIDDEN_BOUNDARY = "sampling_forbidden_boundary"
# Hypothesis engine / self-experimentation (Prompt 25).
HYPOTHESIS_EXPLOSION = "hypothesis_explosion"
TOO_MANY_INCONCLUSIVE_TESTS = "too_many_inconclusive_tests"
REPEATED_UNSAFE_HYPOTHESES = "repeated_unsafe_hypotheses"
EXCESSIVE_INTERVENTION_RATE = "excessive_intervention_rate"
NO_HYPOTHESIS_PROGRESS = "no_hypothesis_progress"
# Auto-regeneration / self-repair (Prompt 26).
CRITICAL_DEGRADATION = "critical_degradation"
REPAIR_LOOP = "repair_loop"
REPEATED_HARMFUL_REPAIRS = "repeated_harmful_repairs"
UNRECOVERABLE_CHECKPOINT = "unrecoverable_checkpoint_inconsistency"
MEMORY_BLOAT_UNRESOLVED = "memory_bloat_unresolved"
SYMBOL_EXPLOSION_UNRESOLVED = "symbol_explosion_unresolved"
WORLD_MODEL_CONTRADICTION_UNRESOLVED = "world_model_contradiction_unresolved"
# LOGOS fracture/synthesis and complexity regulation (Prompt 27).
RUNAWAY_COMPLEXITY = "runaway_complexity"
INERT_SIMPLICITY = "inert_simplicity"
ESC_REPEATED = "esc_repeated"
UNRESOLVED_HIGH_SEVERITY_TENSION = "unresolved_high_severity_tension"
FAILED_SYNTHESIS_LOOP = "failed_synthesis_loop"
CONTRADICTION_EXPLOSION = "contradiction_explosion"

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
    EGO_BOUNDARY_VIOLATION, IDENTITY_ANCHOR_MISMATCH, PERSPECTIVE_STUCK,
    ATTRIBUTION_CONFLICT, SUGGESTION_COMMITTED_MISMATCH,
    COUNTERFACTUAL_BOUNDARY_LEAK,
    ECOLOGY_STIMULUS_RATE_HIGH, ECOLOGY_SILENCE_TOO_LONG,
    ECOLOGY_ANOMALY_RATE_HIGH, ECOLOGY_MEMORY_GROWTH,
    ECOLOGY_REPLAY_MISMATCH,
    CURIOSITY_RUNAWAY, SAMPLING_LOOP, EXCESSIVE_NOVELTY_SEEKING,
    NO_USEFUL_SAMPLING, SAMPLING_FORBIDDEN_BOUNDARY,
    HYPOTHESIS_EXPLOSION, TOO_MANY_INCONCLUSIVE_TESTS,
    REPEATED_UNSAFE_HYPOTHESES, EXCESSIVE_INTERVENTION_RATE,
    NO_HYPOTHESIS_PROGRESS,
    CRITICAL_DEGRADATION, REPAIR_LOOP, REPEATED_HARMFUL_REPAIRS,
    UNRECOVERABLE_CHECKPOINT, MEMORY_BLOAT_UNRESOLVED,
    SYMBOL_EXPLOSION_UNRESOLVED, WORLD_MODEL_CONTRADICTION_UNRESOLVED,
    RUNAWAY_COMPLEXITY, INERT_SIMPLICITY, ESC_REPEATED,
    UNRESOLVED_HIGH_SEVERITY_TENSION, FAILED_SYNTHESIS_LOOP,
    CONTRADICTION_EXPLOSION,
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
