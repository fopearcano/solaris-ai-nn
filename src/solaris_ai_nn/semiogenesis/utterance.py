"""Internal utterances -- structured sign sequences used internally, not speech.

An :class:`InternalUtterance` is a structured sequence/graph of signs (e.g. "sign A
predicts sign B", "absence sign increases attention toward echo sign"). It is NOT
human speech; it may be rendered as human-readable debug text in reports, and any
such rendering is explicitly marked as a gloss.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .private_syntax import PrivateSyntaxPattern


class UtteranceKind:
    MEMORY_TRACE = "memory_trace_utterance"
    PREDICTION = "prediction_utterance"
    ATTENTION = "attention_utterance"
    ABSENCE = "absence_utterance"
    LOGOS_TENSION = "LOGOS_tension_utterance"
    HYPOTHESIS = "hypothesis_utterance"
    CONSOLIDATION = "consolidation_utterance"
    UNKNOWN = "unknown_utterance"

    ALL = (MEMORY_TRACE, PREDICTION, ATTENTION, ABSENCE, LOGOS_TENSION,
           HYPOTHESIS, CONSOLIDATION, UNKNOWN)


@dataclass
class InternalUtterance:
    """A structured sequence/graph of signs (internal, not human speech)."""

    kind: str
    sign_sequence: List[str] = field(default_factory=list)
    relation: str = ""
    utterance_id: str = field(
        default_factory=lambda: f"UTT_{uuid.uuid4().hex[:8]}")
    pattern_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    debug_gloss: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "utterance_id": self.utterance_id,
            "kind": self.kind,
            "sign_sequence": list(self.sign_sequence),
            "relation": self.relation,
            "pattern_refs": list(self.pattern_refs),
            "confidence": round(self.confidence, 4),
            "debug_gloss": self.debug_gloss,
            "metadata": dict(self.metadata),
            "note": "internal sign structure, not human speech; any debug "
                    "rendering is an approximate gloss",
        }


@dataclass
class UtteranceBuilder:
    """Builds internal utterances from private-syntax patterns."""

    utterances: List[InternalUtterance] = field(default_factory=list)

    def build(self, patterns: List[PrivateSyntaxPattern], *,
              max_utterances: int = 50) -> List[InternalUtterance]:
        self.utterances = []
        for pat in patterns:
            if len(self.utterances) >= max_utterances:
                break
            kind = self._kind_for(pat.relation)
            # The debug gloss is explicitly marked as an approximation, not speech.
            gloss = self._gloss(pat)
            self.utterances.append(InternalUtterance(
                kind=kind, sign_sequence=list(pat.signs),
                relation=pat.relation, pattern_refs=[pat.pattern_id],
                confidence=pat.strength, debug_gloss=gloss,
                metadata={"support": pat.support}))
        return self.utterances

    @staticmethod
    def _kind_for(relation: str) -> str:
        if relation in ("predicts",):
            return UtteranceKind.PREDICTION
        if relation in ("before_absence", "after_absence"):
            return UtteranceKind.ABSENCE
        if relation in ("contradicts", "splits"):
            return UtteranceKind.LOGOS_TENSION
        if relation in ("amplifies", "inhibits"):
            return UtteranceKind.ATTENTION
        return UtteranceKind.MEMORY_TRACE

    @staticmethod
    def _gloss(pattern: PrivateSyntaxPattern) -> str:
        seq = " ".join(pattern.signs)
        return f"[gloss~approx] {seq} ({pattern.relation})"

    def to_dict(self) -> Dict[str, Any]:
        return {"utterance_count": len(self.utterances),
                "utterances": [u.to_dict() for u in self.utterances]}
