"""LOGOS tension model -- opposition as productive cognitive pressure.

A :class:`LogosTension` is a detected *opposition* between two internal poles
(known vs unknown, habit vs novelty, support vs contradiction, ...). A
tension is **not** an error by default: some tensions should be preserved.
LOGOS is a tension engine, never an authority -- it exposes fracture and
proposes bounded resolution paths, it does not decide truth.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TensionType:
    KNOWN_UNKNOWN = "known_unknown"
    HABIT_NOVELTY = "habit_novelty"
    EXPLORE_STABILIZE = "explore_stabilize"
    ACTION_INHIBITION = "action_inhibition"
    NEED_SAFETY = "need_safety"
    SYMBOL_AMBIGUITY = "symbol_ambiguity"
    WORLD_MODEL_CONTRADICTION = "world_model_contradiction"
    PREDICTION_FAILURE = "prediction_failure"
    MYSTERIUM_SYNTHESIS = "mysterium_synthesis"
    MEMORY_COMPRESSION = "memory_compression"
    GROWTH_STAGNATION = "growth_stagnation"
    DRIFT_IDENTITY = "drift_identity"
    REGULARITY_ANOMALY = "regularity_anomaly"
    HYPOTHESIS_CONFLICT = "hypothesis_conflict"
    SELF_OTHER_BOUNDARY = "self_other_boundary"
    OFFLINE_REAL_BOUNDARY = "offline_real_boundary"
    COMPLEXITY_OVERLOAD = "complexity_overload"
    INERT_SIMPLICITY = "inert_simplicity"

    ALL = (KNOWN_UNKNOWN, HABIT_NOVELTY, EXPLORE_STABILIZE,
           ACTION_INHIBITION, NEED_SAFETY, SYMBOL_AMBIGUITY,
           WORLD_MODEL_CONTRADICTION, PREDICTION_FAILURE,
           MYSTERIUM_SYNTHESIS, MEMORY_COMPRESSION, GROWTH_STAGNATION,
           DRIFT_IDENTITY, REGULARITY_ANOMALY, HYPOTHESIS_CONFLICT,
           SELF_OTHER_BOUNDARY, OFFLINE_REAL_BOUNDARY, COMPLEXITY_OVERLOAD,
           INERT_SIMPLICITY)
    # Tensions where a safety/boundary pole dominates a curiosity pole.
    SAFETY_DOMINANT = frozenset({NEED_SAFETY, ACTION_INHIBITION,
                                 SELF_OTHER_BOUNDARY, OFFLINE_REAL_BOUNDARY})


class TensionPolarity:
    """Canonical pole names used for ``polarity_a`` / ``polarity_b``."""

    KNOWN = "known"
    UNKNOWN = "unknown"
    HABIT = "habit"
    NOVELTY = "novelty"
    EXPLORE = "explore"
    STABILIZE = "stabilize"
    ACTION = "action_pressure"
    INHIBITION = "inhibition"
    NEED = "need_pressure"
    SAFETY = "safety_boundary"
    STABLE = "stable"
    AMBIGUOUS = "ambiguous"
    SUPPORT = "support"
    CONTRADICTION = "contradiction"
    CONFIDENCE = "confidence"
    FAILURE = "failure"
    MYSTERIUM = "mysterium"
    SYNTHESIS = "synthesis"
    ACCUMULATION = "accumulation"
    COMPRESSION = "compression"
    GROWTH = "growth"
    STAGNATION = "stagnation"
    DRIFT = "drift"
    IDENTITY = "identity"
    REGULARITY = "regularity"
    ANOMALY = "anomaly"
    SELF = "self"
    OTHER = "external"
    OFFLINE = "offline"
    REAL = "real"
    SIMPLE = "simple"
    COMPLEX = "complex"


class TensionSeverity:
    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    HIGH = "high"

    ALL = (INFO, WATCH, WARNING, HIGH)
    ORDER = {INFO: 0, WATCH: 1, WARNING: 2, HIGH: 3}
    EVIDENCE_REQUIRED = frozenset({WARNING, HIGH})


class TensionStatus:
    DETECTED = "detected"
    PRESERVED = "preserved"
    SPLIT = "split"
    MERGED = "merged"
    SYNTHESIZED = "synthesized"
    PRUNED = "pruned"
    STABILIZED = "stabilized"
    HYPOTHESIS_CREATED = "hypothesis_created"
    SENT_TO_REPLAY = "sent_to_replay"
    SENT_TO_SAMPLING = "sent_to_sampling"
    SENT_TO_REPAIR = "sent_to_repair"
    UNRESOLVED = "unresolved"

    ALL = (DETECTED, PRESERVED, SPLIT, MERGED, SYNTHESIZED, PRUNED,
           STABILIZED, HYPOTHESIS_CREATED, SENT_TO_REPLAY, SENT_TO_SAMPLING,
           SENT_TO_REPAIR, UNRESOLVED)


RISK_LEVELS = ("low", "medium", "high")


@dataclass
class LogosTension:
    """One detected opposition between two internal poles."""

    tension_type: str
    polarity_a: str
    polarity_b: str
    severity: str = TensionSeverity.WATCH
    status: str = TensionStatus.DETECTED
    source_modules: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    related_world_nodes: List[str] = field(default_factory=list)
    related_hypotheses: List[str] = field(default_factory=list)
    related_actions: List[str] = field(default_factory=list)
    expected_resolution_value: float = 0.0
    risk_level: str = "low"
    confidence: float = 0.5
    tension_id: str = field(default_factory=lambda: f"TEN_{uuid.uuid4().hex[:8]}")
    detected_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.tension_type not in TensionType.ALL:
            raise ValueError(f"unknown tension type {self.tension_type!r}")
        if self.severity not in TensionSeverity.ALL:
            raise ValueError(f"unknown tension severity {self.severity!r}")
        if self.status not in TensionStatus.ALL:
            raise ValueError(f"unknown tension status {self.status!r}")
        if self.risk_level not in RISK_LEVELS:
            self.risk_level = "low"
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    @property
    def evidence_ok(self) -> bool:
        """Warning/high tensions must carry evidence refs."""
        if self.severity in TensionSeverity.EVIDENCE_REQUIRED:
            return bool(self.evidence_refs)
        return True

    @property
    def is_safety_dominant(self) -> bool:
        return self.tension_type in TensionType.SAFETY_DOMINANT

    @property
    def dedup_key(self) -> str:
        target = (self.related_world_nodes or self.related_symbols
                  or [self.polarity_a + ":" + self.polarity_b])
        return f"{self.tension_type}:{target[0]}"

    def set_status(self, status: str) -> None:
        if status not in TensionStatus.ALL:
            raise ValueError(f"unknown tension status {status!r}")
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "evidence_ok": self.evidence_ok,
                "is_safety_dominant": self.is_safety_dominant}
