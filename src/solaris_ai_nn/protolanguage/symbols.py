"""Proto-symbols -- internal signs born from repeated experience.

A ProtoSymbol is an internally generated token tied to recorded structure:
a repeated stimulus pattern, an absence state, a habit loop, a persistent
unknown, a boundary, a need, an entity, a decision. Tokens are compact
generated forms (``ABS_0001``, ``HAB_LOOP_0004``) -- never human-language
names as primaries -- and every symbol carries its grounding, its
observation count, and the utility scores (compression, prediction,
stability, ambiguity) that decide whether it earns its keep. None of this
is human language, understanding, or consciousness.
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SymbolType:
    STIMULUS = "stimulus_symbol"
    ABSENCE = "absence_symbol"
    ACTION = "action_symbol"
    REACTION = "reaction_symbol"
    HABIT = "habit_symbol"
    NEED = "need_symbol"
    BOUNDARY = "boundary_symbol"
    UNKNOWN = "unknown_symbol"
    ENTITY = "entity_symbol"
    CONTEXT = "context_symbol"
    LATENT_SCHEMA = "latent_schema_symbol"
    MILESTONE = "milestone_symbol"
    SELF_BOUNDARY = "self_boundary_symbol"
    EXECUTIVE_DECISION = "executive_decision_symbol"

    ALL = (STIMULUS, ABSENCE, ACTION, REACTION, HABIT, NEED, BOUNDARY,
           UNKNOWN, ENTITY, CONTEXT, LATENT_SCHEMA, MILESTONE,
           SELF_BOUNDARY, EXECUTIVE_DECISION)


# Generated-token shape: PREFIX[_QUALIFIER...]_NNNN[_hash4].
TOKEN_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_\d{3,6}(?:_[0-9a-f]{4})?$")

EVIDENCE_KINDS = ("real", "simulated", "offline", "counterfactual")

SYMBOL_NOTE = ("an internal operational sign grounded in recorded "
               "structure; not human language, not understanding, not "
               "consciousness")


@dataclass
class SymbolGrounding:
    """One tie between a symbol and observed structure."""

    dimension: str  # signal_pattern | context | need_state |
    #                 action_tendency | reaction_valence |
    #                 world_model_node | boundary | latent_schema |
    #                 milestone | mysterium_change | executive_decision
    reference: str = ""
    evidence_kind: str = "real"
    observed_count: int = 1
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.evidence_kind not in EVIDENCE_KINDS:
            raise ValueError(f"unknown evidence kind "
                             f"{self.evidence_kind!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SymbolConfidence:
    """The four utility components and their cautious combination."""

    compression: float = 0.0
    prediction: float = 0.0
    stability: float = 0.0
    ambiguity: float = 0.0  # high ambiguity lowers confidence

    def combined(self) -> float:
        utility = max(self.compression, self.prediction)
        return round(max(0.0, min(0.95,  # never certainty
                                  0.5 * utility + 0.5 * self.stability
                                  - 0.5 * self.ambiguity)), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "combined": self.combined()}


@dataclass
class ProtoSymbol:
    """One internally generated sign with its grounding and utility."""

    token: str
    type: str
    symbol_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    grounding_refs: List[SymbolGrounding] = field(default_factory=list)
    observation_count: int = 0
    compression_score: float = 0.0
    prediction_score: float = 0.0
    stability_score: float = 0.0
    ambiguity_score: float = 0.0
    confidence: float = 0.0
    status: str = "active"  # active | ambiguous | stale | merged | extinct
    debug_label: str = ""  # secondary, inspection-only
    source_modules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in SymbolType.ALL:
            raise ValueError(f"unknown symbol type {self.type!r}")
        if not TOKEN_PATTERN.match(self.token):
            raise ValueError(
                f"token {self.token!r} is not a generated form; "
                "human-language names cannot be primary tokens")

    # -- life ---------------------------------------------------------------------

    def observe(self, evidence_ref: str,
                evidence_kind: str = "real",
                dimension: str = "signal_pattern") -> None:
        self.observation_count += 1
        self.updated_at = time.time()
        for grounding in self.grounding_refs:
            if grounding.reference == evidence_ref \
                    and grounding.dimension == dimension:
                grounding.observed_count += 1
                return
        self.grounding_refs.append(SymbolGrounding(
            dimension=dimension, reference=str(evidence_ref),
            evidence_kind=evidence_kind))
        self.grounding_refs = self.grounding_refs[-20:]

    def recompute_confidence(self) -> float:
        self.confidence = SymbolConfidence(
            compression=self.compression_score,
            prediction=self.prediction_score,
            stability=self.stability_score,
            ambiguity=self.ambiguity_score).combined()
        return self.confidence

    @property
    def stable(self) -> bool:
        return (self.status == "active"
                and self.observation_count >= 5
                and self.stability_score >= 0.6
                and self.ambiguity_score < 0.5)

    @property
    def offline_born(self) -> bool:
        return bool(self.metadata.get("offline", False))

    def to_dict(self) -> Dict[str, Any]:
        data = {k: v for k, v in self.__dict__.items()
                if k != "grounding_refs"}
        data["grounding_refs"] = [g.to_dict()
                                  for g in self.grounding_refs]
        data["stable"] = self.stable
        data["note"] = SYMBOL_NOTE
        return data
