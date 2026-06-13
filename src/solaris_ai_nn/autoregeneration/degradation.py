"""Degradation model -- operational signals that runtime state is decaying.

A :class:`DegradationSignal` is an *operational* finding (memory bloat,
stale traces, contradictory graph fragments, runaway habits, drift, identity
gaps), never an illness. Warning/critical signals must carry evidence refs.
The model is data only; diagnostics produce it and the repair policy reads
it. Nothing here mutates state.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DegradationType:
    MEMORY_BLOAT = "memory_bloat"
    STATE_FILE_CORRUPTION = "state_file_corruption"
    CHECKPOINT_INCONSISTENCY = "checkpoint_inconsistency"
    BROKEN_REFERENCE = "broken_reference"
    TELEMETRY_OVERGROWTH = "telemetry_overgrowth"
    SYMBOL_EXPLOSION = "symbol_explosion"
    SYMBOL_STALENESS = "symbol_staleness"
    WORLD_MODEL_CONTRADICTION = "world_model_contradiction"
    WORLD_MODEL_EDGE_DECAY = "world_model_edge_decay"
    HABIT_DEAD_LOOP = "habit_dead_loop"
    HABIT_RUNAWAY = "habit_runaway"
    PREDICTION_DEGRADATION = "prediction_degradation"
    MYSTERIUM_SATURATION = "mysterium_saturation"
    EXECUTIVE_LOOP = "executive_loop"
    HOMEOSTATIC_INSTABILITY = "homeostatic_instability"
    DRIFT_RUNAWAY = "drift_runaway"
    DEVELOPMENTAL_STAGNATION = "developmental_stagnation"
    HYPOTHESIS_INCONCLUSIVE_LOOP = "hypothesis_inconclusive_loop"
    UNSAFE_SAMPLING_REPETITION = "unsafe_sampling_repetition"
    IDENTITY_CONTINUITY_GAP = "identity_continuity_gap"
    UNKNOWN = "unknown"

    ALL = (MEMORY_BLOAT, STATE_FILE_CORRUPTION, CHECKPOINT_INCONSISTENCY,
           BROKEN_REFERENCE, TELEMETRY_OVERGROWTH, SYMBOL_EXPLOSION,
           SYMBOL_STALENESS, WORLD_MODEL_CONTRADICTION,
           WORLD_MODEL_EDGE_DECAY, HABIT_DEAD_LOOP, HABIT_RUNAWAY,
           PREDICTION_DEGRADATION, MYSTERIUM_SATURATION, EXECUTIVE_LOOP,
           HOMEOSTATIC_INSTABILITY, DRIFT_RUNAWAY, DEVELOPMENTAL_STAGNATION,
           HYPOTHESIS_INCONCLUSIVE_LOOP, UNSAFE_SAMPLING_REPETITION,
           IDENTITY_CONTINUITY_GAP, UNKNOWN)
    # Degradations that touch identity continuity -> governance caution.
    IDENTITY_AFFECTING = frozenset({CHECKPOINT_INCONSISTENCY,
                                    IDENTITY_CONTINUITY_GAP})


class DegradationSeverity:
    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"

    ALL = (INFO, WATCH, WARNING, CRITICAL)
    ORDER = {INFO: 0, WATCH: 1, WARNING: 2, CRITICAL: 3}
    # Severities that demand evidence refs.
    EVIDENCE_REQUIRED = frozenset({WARNING, CRITICAL})


@dataclass
class DegradationSignal:
    """One operational degradation finding (never an 'illness')."""

    type: str
    severity: str = DegradationSeverity.WATCH
    source_module: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    metric_snapshot: Dict[str, Any] = field(default_factory=dict)
    probable_causes: List[str] = field(default_factory=list)
    repairable: bool = True
    requires_governance: bool = False
    signal_id: str = field(default_factory=lambda: f"DEG_{uuid.uuid4().hex[:8]}")
    detected_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in DegradationType.ALL:
            raise ValueError(f"unknown degradation type {self.type!r}")
        if self.severity not in DegradationSeverity.ALL:
            raise ValueError(f"unknown severity {self.severity!r}")
        # Identity-affecting degradation always needs governance to repair.
        if self.type in DegradationType.IDENTITY_AFFECTING:
            self.requires_governance = True

    @property
    def evidence_ok(self) -> bool:
        """Warning/critical signals must carry evidence refs."""
        if self.severity in DegradationSeverity.EVIDENCE_REQUIRED:
            return bool(self.evidence_refs)
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "evidence_ok": self.evidence_ok}


@dataclass
class DegradationState:
    """The aggregated degradation picture from one diagnostics pass."""

    signals: List[DegradationSignal] = field(default_factory=list)
    scanned_at: float = field(default_factory=time.time)

    def add(self, signal: DegradationSignal) -> None:
        self.signals.append(signal)

    def worst_severity(self) -> str:
        if not self.signals:
            return DegradationSeverity.INFO
        return max((s.severity for s in self.signals),
                   key=lambda s: DegradationSeverity.ORDER[s])

    def by_severity(self, severity: str) -> List[DegradationSignal]:
        return [s for s in self.signals if s.severity == severity]

    def critical(self) -> List[DegradationSignal]:
        return self.by_severity(DegradationSeverity.CRITICAL)

    def repairable(self) -> List[DegradationSignal]:
        return [s for s in self.signals if s.repairable]

    def ranked(self) -> List[DegradationSignal]:
        return sorted(self.signals,
                      key=lambda s: DegradationSeverity.ORDER[s.severity],
                      reverse=True)

    def counts_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in self.signals:
            counts[s.type] = counts.get(s.type, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_count": len(self.signals),
            "worst_severity": self.worst_severity(),
            "counts_by_type": self.counts_by_type(),
            "critical_count": len(self.critical()),
            "signals": [s.to_dict() for s in self.ranked()],
        }
