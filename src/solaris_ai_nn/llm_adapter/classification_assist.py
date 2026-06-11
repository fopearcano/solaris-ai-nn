"""LLM classification assist -- suggestions under a deterministic ruler.

The deterministic classifier is authoritative, always. The LLM may only
*suggest* a kind for text the classifier marked unknown; if the
deterministic verdict is unsafe nothing can override it; if the suggestion
is higher-risk than the deterministic verdict the safer class wins; and a
suggested command class still travels the normal confirmation/governance
path -- the suggestion creates no command by itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .base import LLMAdapter, LLMRequest, LLMTaskType

# Lower index = safer. Anything not listed is treated as highest risk.
RISK_ORDER = (
    "unknown", "state_query", "explanation_query", "operator_note",
    "report_request", "sensory_text_stimulus", "bounded_command_request",
    "governance_rejection", "governance_approval",
    "emergency_stop_request", "unsafe_request",
)

_SUGGESTION_RE = re.compile(
    r"kind=(\w+)\s+confidence=([0-9.]+)\s+reason=(.+)")


def risk_rank(kind: str) -> int:
    try:
        return RISK_ORDER.index(kind)
    except ValueError:
        return len(RISK_ORDER)


@dataclass
class ClassificationSuggestion:
    """A suggestion with its provenance; never a decision."""

    kind: str = "unknown"
    confidence: float = 0.0
    reason: str = ""
    source: str = "llm_adapter"
    overrode_deterministic: bool = False  # structurally always False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LLMClassificationAssistant:
    """Suggest-only assistant beside the deterministic classifier."""

    adapter: LLMAdapter
    suggestions_made: int = field(default=0, init=False)
    disagreements: int = field(default=0, init=False)
    overrides_blocked: int = field(default=0, init=False)

    def suggest_classification(self, text: str,
                               deterministic_classification: Any,
                               context: Optional[Dict[str, Any]] = None,
                               ) -> ClassificationSuggestion:
        det_kind = getattr(deterministic_classification, "kind",
                           str(deterministic_classification))
        if det_kind == "unsafe_request":
            # Nothing to suggest: unsafe is final.
            self.overrides_blocked += 1
            return ClassificationSuggestion(
                kind="unsafe_request", confidence=1.0,
                reason="the deterministic classifier marked the input "
                       "unsafe; no suggestion can override that",
                source="deterministic")
        request = LLMRequest(
            task_type=LLMTaskType.CLASSIFICATION_ASSIST,
            input_text=str(text),
            allowed_facts=[f"valid kinds: {', '.join(RISK_ORDER[:-1])}"],
            grounded_context=dict(context or {}))
        response = self.adapter.generate(request)
        self.suggestions_made += 1
        if response.refused:
            return ClassificationSuggestion(
                kind="unknown", confidence=0.0,
                reason=f"adapter unavailable: {response.refusal_reason}")
        match = _SUGGESTION_RE.search(response.output_text)
        if not match or match.group(1) not in RISK_ORDER:
            return ClassificationSuggestion(
                kind="unknown", confidence=0.0,
                reason="the suggestion did not match the required format")
        return ClassificationSuggestion(
            kind=match.group(1),
            confidence=max(0.0, min(1.0, float(match.group(2)))),
            reason=match.group(3).strip()[:120])

    def resolve_with_deterministic(
            self, deterministic_classification: Any,
            suggestion: ClassificationSuggestion) -> str:
        """The final kind. Deterministic wins; ties break toward safety."""
        det_kind = getattr(deterministic_classification, "kind",
                           str(deterministic_classification))
        if det_kind == "unsafe_request":
            self.overrides_blocked += 1
            return det_kind
        if det_kind != "unknown":
            if suggestion.kind != det_kind:
                self.disagreements += 1
            return det_kind  # a confident deterministic verdict stands
        # Deterministic said unknown: a *safer-or-equal-risk* suggestion
        # may fill in; higher-risk suggestions stay unknown (and would
        # need the normal confirmation path anyway).
        if suggestion.confidence < 0.5:
            return "unknown"
        if risk_rank(suggestion.kind) > risk_rank(
                "bounded_command_request"):
            self.disagreements += 1
            self.overrides_blocked += 1
            return "unknown"
        return suggestion.kind

    def snapshot(self) -> Dict[str, Any]:
        return {
            "adapter": self.adapter.name,
            "suggestions_made": self.suggestions_made,
            "disagreements": self.disagreements,
            "overrides_blocked": self.overrides_blocked,
            "note": "the deterministic classifier is authoritative; "
                    "suggestions only ever fill in 'unknown' with "
                    "lower-risk kinds",
        }
