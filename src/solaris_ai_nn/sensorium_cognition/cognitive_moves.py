"""Cognitive moves -- bounded operations over signs, concepts, and relations.

A :class:`CognitiveMove` is one operation over internal signs, proto-concepts,
relations, memory traces, hypotheses, and LOGOS tensions. Moves preserve evidence,
never fabricate sensory evidence, cannot act on the external world, and can
recommend *internal attention* only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class CognitiveMoveType:
    PREDICT_NEXT_SIGN = "predict_next_sign"
    PREDICT_ABSENCE = "predict_absence"
    RETRIEVE_RELATED_SIGN = "retrieve_related_sign"
    COMPARE_SIGNS = "compare_signs"
    MERGE_SIGN_CANDIDATES = "merge_sign_candidates"
    SPLIT_AMBIGUOUS_SIGN = "split_ambiguous_sign"
    TEST_RELATION = "test_relation"
    SIMULATE_SEQUENCE = "simulate_sequence"
    GENERATE_QUESTION_PRESSURE = "generate_question_pressure"
    RESOLVE_OR_ESCALATE_TENSION = "resolve_or_escalate_tension"
    SELECT_ATTENTION_TARGET = "select_attention_target"
    RECOMMEND_CONSOLIDATION = "recommend_consolidation"
    MARK_UNKNOWN = "mark_unknown"
    DEFER_AS_AMBIGUOUS = "defer_as_ambiguous"

    ALL = (PREDICT_NEXT_SIGN, PREDICT_ABSENCE, RETRIEVE_RELATED_SIGN,
           COMPARE_SIGNS, MERGE_SIGN_CANDIDATES, SPLIT_AMBIGUOUS_SIGN,
           TEST_RELATION, SIMULATE_SEQUENCE, GENERATE_QUESTION_PRESSURE,
           RESOLVE_OR_ESCALATE_TENSION, SELECT_ATTENTION_TARGET,
           RECOMMEND_CONSOLIDATION, MARK_UNKNOWN, DEFER_AS_AMBIGUOUS)


@dataclass
class CognitiveMove:
    """One bounded operational move over signs/concepts/relations (not a sentence)."""

    move_type: str
    move_id: str = field(default_factory=lambda: f"MOVE_{uuid.uuid4().hex[:8]}")
    input_sign_refs: List[str] = field(default_factory=list)
    input_concept_refs: List[str] = field(default_factory=list)
    input_hypothesis_refs: List[str] = field(default_factory=list)
    input_tension_refs: List[str] = field(default_factory=list)
    input_memory_refs: List[str] = field(default_factory=list)
    result_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    uncertainty: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.limitations:
            self.limitations = [
                "operational move over signs/concepts, not a sentence or "
                "proof of understanding",
                "recommends internal attention only; cannot act on the external "
                "world",
            ]

    @property
    def recommends_attention(self) -> bool:
        return self.move_type in (CognitiveMoveType.SELECT_ATTENTION_TARGET,
                                  CognitiveMoveType.GENERATE_QUESTION_PRESSURE)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "move_id": self.move_id,
            "move_type": self.move_type,
            "input_sign_refs": list(self.input_sign_refs),
            "input_concept_refs": list(self.input_concept_refs),
            "input_hypothesis_refs": list(self.input_hypothesis_refs),
            "input_tension_refs": list(self.input_tension_refs),
            "input_memory_refs": list(self.input_memory_refs),
            "result_refs": list(self.result_refs),
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "note": "operational cognitive move; internal-only, no external "
                    "action",
        }


@dataclass
class CognitiveMoveResult:
    """The outcome of applying a move (recommendation/marker, never actuation)."""

    move_id: str
    move_type: str
    outcome: str  # "recommendation" | "marker" | "prediction" | "deferral"
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"move_id": self.move_id, "move_type": self.move_type,
                "outcome": self.outcome, "detail": dict(self.detail),
                "note": "internal recommendation/marker only; never external "
                        "actuation"}
