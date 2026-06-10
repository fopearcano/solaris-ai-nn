"""Deterministic internal query interface -- normalized string matching only.

This is a command layer, not chatbot intelligence: a fixed set of normalized
question strings maps to explanation-engine methods. Unknown queries return an
honest "does not know" fallback. No parsing beyond lowercasing and stripping
punctuation; no LLM anywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from .schemas import Explanation, ExplanationContext, QueryResult


def normalize(query: str) -> str:
    """Lowercase, strip punctuation/extra spaces."""
    text = re.sub(r"[?!.,;:]+", "", str(query).lower())
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class QueryInterface:
    """Maps a fixed set of internal queries to grounded explanations."""

    engine: "ExplanationEngine" = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.engine is None:
            from .explanation import ExplanationEngine

            self.engine = ExplanationEngine()
        e = self.engine
        self._handlers: Dict[str, Callable[[ExplanationContext], Explanation]] = {
            "what happened last": e.explain_last_event,
            "why was the last action suggested": e.explain_action_suggestion,
            "why was the last action blocked": e.explain_blocked_action,
            "what changed in the substrate": e.explain_substrate,
            "what habit is strongest": e.explain_strongest_habit,
            "what was pruned": e.explain_pruning,
            "what did plasticity change": e.explain_plasticity,
            "what does the inner map currently track": e.explain_inner_map,
            "what happened during silence": e.explain_silence,
            "did the system restart": e.explain_continuity,
            "what is the current body state": e.explain_embodiment,
        }

    def supported_queries(self) -> List[str]:
        return sorted(self._handlers)

    def answer(self, query: str, context: ExplanationContext) -> QueryResult:
        """Answer one query deterministically; unknown -> safe fallback."""
        key = normalize(query)
        handler = self._handlers.get(key)
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        explanation = handler(context)
        return QueryResult(
            query=query,
            answered=explanation.confidence > 0.0,
            text=explanation.text,
            data=explanation.to_dict(),
            confidence=explanation.confidence,
        )
