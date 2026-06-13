"""Hypothesis schema -- grounded, testable internal research artifacts.

A :class:`Hypothesis` is an *internal research artifact*, never a belief: a
deterministic, grounded statement of the form "pattern X may predict Y",
carrying what would count as supporting, alternative, and falsifying
observation, the bounded scope it may be tested in, and a confidence that
only moves on evidence. No LLM generates these; nothing here claims the
system "believes", "wants", or "understands".
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class HypothesisType:
    PREDICTION = "prediction_hypothesis"
    CAUSAL_CANDIDATE = "causal_candidate_hypothesis"
    DELAYED_CONSEQUENCE = "delayed_consequence_hypothesis"
    PROTO_SYMBOL_GROUNDING = "proto_symbol_grounding_hypothesis"
    PROTO_SYNTAX = "proto_syntax_hypothesis"
    HABIT_CONTEXT = "habit_context_hypothesis"
    BOUNDARY = "boundary_hypothesis"
    MYSTERIUM_REDUCTION = "mysterium_reduction_hypothesis"
    STAGNATION_RECOVERY = "stagnation_recovery_hypothesis"
    HOMEOSTATIC_REGULATION = "homeostatic_regulation_hypothesis"
    EXECUTIVE_ARBITRATION = "executive_arbitration_hypothesis"
    WORLD_MODEL_EDGE = "world_model_edge_hypothesis"
    ANOMALY_PATTERN = "anomaly_pattern_hypothesis"

    ALL = (PREDICTION, CAUSAL_CANDIDATE, DELAYED_CONSEQUENCE,
           PROTO_SYMBOL_GROUNDING, PROTO_SYNTAX, HABIT_CONTEXT, BOUNDARY,
           MYSTERIUM_REDUCTION, STAGNATION_RECOVERY, HOMEOSTATIC_REGULATION,
           EXECUTIVE_ARBITRATION, WORLD_MODEL_EDGE, ANOMALY_PATTERN)


class HypothesisStatus:
    PROPOSED = "proposed"
    SCHEDULED = "scheduled"
    TESTING = "testing"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"
    UNSAFE_TO_TEST = "unsafe_to_test"
    EXPIRED = "expired"

    ALL = (PROPOSED, SCHEDULED, TESTING, SUPPORTED, WEAKENED, FALSIFIED,
           INCONCLUSIVE, UNSAFE_TO_TEST, EXPIRED)
    # Terminal-ish statuses that should not be re-scheduled automatically.
    CLOSED = frozenset({FALSIFIED, EXPIRED})


class HypothesisScope:
    """The bounded scope a hypothesis may be tested in (never real-world)."""

    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    NURSERY_ONLY = "nursery_only"
    LATENT_REPLAY_ONLY = "latent_replay_only"
    READ_ONLY_STREAM = "read_only_stream"
    SIDECAR_OBSERVE_ONLY = "sidecar_observe_only"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, NURSERY_ONLY, LATENT_REPLAY_ONLY,
           READ_ONLY_STREAM, SIDECAR_OBSERVE_ONLY)


class HypothesisConfidence:
    """Confidence bands and bounded confidence arithmetic (not belief)."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

    # Confidence never jumps; each update is bounded to this step.
    MAX_STEP = 0.2

    @staticmethod
    def band(value: float) -> str:
        if value >= 0.75:
            return HypothesisConfidence.HIGH
        if value >= 0.5:
            return HypothesisConfidence.MODERATE
        if value >= 0.25:
            return HypothesisConfidence.LOW
        return HypothesisConfidence.VERY_LOW

    @staticmethod
    def bounded_update(current: float, delta: float) -> float:
        step = max(-HypothesisConfidence.MAX_STEP,
                   min(HypothesisConfidence.MAX_STEP, float(delta)))
        return round(max(0.0, min(1.0, current + step)), 4)


RISK_LEVELS = ("low", "medium", "high")


@dataclass
class Hypothesis:
    """One grounded, testable hypothesis candidate (never a belief)."""

    type: str
    statement: str
    expected_observation: str = ""
    alternative_observation: str = ""
    source_refs: List[str] = field(default_factory=list)
    testable: bool = True
    required_scope: str = HypothesisScope.INTERNAL_ONLY
    confidence: float = 0.3
    uncertainty: float = 0.7
    risk_level: str = "low"
    priority: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)
    status: str = HypothesisStatus.PROPOSED
    hypothesis_id: str = field(
        default_factory=lambda: f"HYP_{uuid.uuid4().hex[:8]}")
    generated_at: float = field(default_factory=time.time)
    target_ref: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in HypothesisType.ALL:
            raise ValueError(f"unknown hypothesis type {self.type!r}")
        if self.status not in HypothesisStatus.ALL:
            raise ValueError(f"unknown hypothesis status {self.status!r}")
        if self.required_scope not in HypothesisScope.ALL:
            raise ValueError(f"unknown hypothesis scope "
                             f"{self.required_scope!r}")
        if self.risk_level not in RISK_LEVELS:
            self.risk_level = "low"
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        self.uncertainty = max(0.0, min(1.0, float(self.uncertainty)))

    @property
    def confidence_band(self) -> str:
        return HypothesisConfidence.band(self.confidence)

    @property
    def dedup_key(self) -> str:
        """A stable key so the same hypothesis is not regenerated."""
        return f"{self.type}:{self.target_ref or self.statement[:48]}"

    def set_status(self, status: str) -> None:
        if status not in HypothesisStatus.ALL:
            raise ValueError(f"unknown hypothesis status {status!r}")
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "confidence_band": self.confidence_band}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
