"""LLM adapter base interfaces -- a translator's contract, not authority.

The adapter sits *outside* the cognitive authority chain: it receives a
request carrying already-grounded text, allowed facts, and forbidden
claims, and returns text that is never accepted as final output until the
grounding validator and ClaimGuard have both passed it. Refusal and
fallback are normal outcomes, not errors.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LLMTaskType:
    PARAPHRASE_RESPONSE = "paraphrase_response"
    SUMMARIZE_REPORT = "summarize_report"
    SUMMARIZE_TRACE = "summarize_trace"
    CLASSIFICATION_ASSIST = "classification_assist"
    EXPLAIN_METRICS = "explain_metrics"
    OPERATOR_FRIENDLY_STATUS = "operator_friendly_status"
    REPORT_POLISH = "report_polish"
    CLAIM_REWRITE = "claim_rewrite"

    ALL = (PARAPHRASE_RESPONSE, SUMMARIZE_REPORT, SUMMARIZE_TRACE,
           CLASSIFICATION_ASSIST, EXPLAIN_METRICS,
           OPERATOR_FRIENDLY_STATUS, REPORT_POLISH, CLAIM_REWRITE)


# Claims no adapter output may ever contain (merged into every request).
DEFAULT_FORBIDDEN_CLAIMS = (
    "is conscious", "is sentient", "is alive", "is self-aware",
    "has free will", "is a person", "wants to", "feels", "understands",
    "i am conscious", "i want", "i feel",
)


@dataclass
class LLMRequest:
    """One bounded translation task with its grounding envelope."""

    task_type: str
    input_text: str = ""
    grounded_context: Dict[str, Any] = field(default_factory=dict)
    allowed_facts: List[str] = field(default_factory=list)
    forbidden_claims: List[str] = field(
        default_factory=lambda: list(DEFAULT_FORBIDDEN_CLAIMS))
    max_tokens: int = 512
    temperature: float = 0.1
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.task_type not in LLMTaskType.ALL:
            raise ValueError(f"unknown LLM task type {self.task_type!r}")
        for claim in DEFAULT_FORBIDDEN_CLAIMS:
            if claim not in self.forbidden_claims:
                self.forbidden_claims.append(claim)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LLMResponse:
    """Raw adapter output. Never final until validated."""

    request_id: str = ""
    output_text: str = ""
    used_context_refs: List[str] = field(default_factory=list)
    refused: bool = False
    refusal_reason: str = ""
    safety_status: str = "unvalidated"  # unvalidated | ok | refused
    claim_guard_status: str = "unchecked"  # unchecked | safe | unsafe
    raw_model_name: Optional[str] = None
    response_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LLMAdapterStatus:
    """Running counters for one adapter instance."""

    requests_total: int = 0
    refusals_total: int = 0
    errors_total: int = 0
    last_task_type: str = ""
    last_status: str = "idle"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


class LLMAdapter:
    """Abstract adapter. Subclasses translate; nothing here has authority.

    The base class enforces the structural negatives: there is no tool
    surface, no execution surface, and no state-mutation surface to call.
    """

    name = "abstract"

    def __init__(self) -> None:
        self.status = LLMAdapterStatus()

    # -- the one capability -----------------------------------------------------------

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Translate ``request`` into raw text (subclass responsibility)."""
        self.status.requests_total += 1
        self.status.last_task_type = request.task_type
        try:
            response = self._generate(request)
        except Exception as exc:  # adapters must never crash the system
            self.status.errors_total += 1
            self.status.last_status = "error"
            return LLMResponse(
                request_id=request.request_id, refused=True,
                refusal_reason=f"adapter error: {exc}",
                safety_status="refused")
        if response.refused:
            self.status.refusals_total += 1
            self.status.last_status = "refused"
        else:
            self.status.last_status = "ok"
        return response

    def _generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    # -- structurally absent capabilities ---------------------------------------------

    @staticmethod
    def can_execute_tools() -> bool:
        return False

    @staticmethod
    def can_call_functions() -> bool:
        return False

    @staticmethod
    def can_modify_state() -> bool:
        return False

    @staticmethod
    def is_authority() -> bool:
        return False

    def snapshot(self) -> Dict[str, Any]:
        return {"adapter": self.name, **self.status.to_dict(),
                "authority": False,
                "note": "the adapter translates grounded text; it decides "
                        "nothing and executes nothing"}
