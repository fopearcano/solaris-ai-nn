"""Proto-utterances -- internal symbolic sequences, never speech.

``[ABS_0001] [NEED_SIGNAL_0002] [ACT_LOOK_0003]`` is an internal
structure built for a purpose (compression, prediction, explanation,
memory, executive support, report support). A human-readable rendering
may be attached, but it is explicitly a *translation* of internal
symbols for inspection -- no "I want", no personhood, no speech.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .symbol_registry import SymbolRegistry

UTTERANCE_PURPOSES = ("compression", "prediction", "explanation",
                      "memory", "executive_support", "report_support")

UTTERANCE_NOTE = ("an internal symbolic structure, not human speech; "
                  "any attached text is a debug translation")

_FORBIDDEN_TRANSLATION_FRAGMENTS = ("i want", "i feel", "i am",
                                    "i think", "i speak")


@dataclass
class ProtoUtterance:
    """One purposeful internal symbol sequence."""

    symbols: List[str]
    purpose: str = "memory"
    context: Dict[str, Any] = field(default_factory=dict)
    grounding_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    human_debug_translation: Optional[str] = None
    utterance_id: str = field(
        default_factory=lambda: uuid.uuid4().hex[:10])
    note: str = UTTERANCE_NOTE
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.purpose not in UTTERANCE_PURPOSES:
            raise ValueError(f"unknown utterance purpose "
                             f"{self.purpose!r}")
        if self.human_debug_translation:
            lowered = self.human_debug_translation.lower()
            for fragment in _FORBIDDEN_TRANSLATION_FRAGMENTS:
                if fragment in lowered:
                    raise ValueError(
                        f"debug translation contains forbidden "
                        f"first-person fragment {fragment!r}")

    def render(self) -> str:
        return " ".join(f"[{token}]" for token in self.symbols)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "rendered": self.render()}


@dataclass
class ProtoUtteranceBuilder:
    """Builds purposeful utterances from registered symbols."""

    registry: SymbolRegistry
    built: int = field(default=0, init=False)
    last_utterance: Optional[ProtoUtterance] = field(default=None,
                                                     init=False)

    def build(self, tokens: List[str], purpose: str = "memory",
              context: Optional[Dict[str, Any]] = None,
              ) -> ProtoUtterance:
        """An utterance from known tokens; confidence follows the
        weakest symbol in it."""
        grounding: List[str] = []
        confidences: List[float] = []
        for token in tokens:
            symbol = self.registry.find_by_token(token)
            if symbol is None:
                raise KeyError(f"unknown symbol token {token!r}; "
                               "utterances are built from registered "
                               "signs only")
            grounding.extend(g.reference
                             for g in symbol.grounding_refs[:2])
            confidences.append(symbol.confidence)
        utterance = ProtoUtterance(
            symbols=list(tokens), purpose=purpose,
            context=dict(context or {}),
            grounding_refs=grounding[:10],
            confidence=round(min(confidences) if confidences else 0.0,
                             4))
        self.built += 1
        self.last_utterance = utterance
        return utterance

    def build_from_sequence(self, sequence: Any,
                            purpose: str = "memory") -> ProtoUtterance:
        return self.build(list(sequence.tokens), purpose=purpose,
                          context={"sequence_count": sequence.count})

    def snapshot(self) -> Dict[str, Any]:
        return {
            "utterances_built": self.built,
            "last": (self.last_utterance.to_dict()
                     if self.last_utterance else None),
            "purposes": list(UTTERANCE_PURPOSES),
            "note": UTTERANCE_NOTE,
        }
