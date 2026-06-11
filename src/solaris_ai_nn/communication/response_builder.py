"""Response builder -- grounded text or an honest refusal, nothing else.

Every response carries evidence references or explicit limitations, is
rendered from a fixed template, and is ClaimGuard-scanned before it leaves
the builder. The builder never says a command was executed when it was
only recorded as a request, and it never says "I want", "I feel", or
"I am conscious" -- structurally, those templates do not exist.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .templates import render

DEFAULT_LIMITATIONS = [
    "Responses are generated from recorded state, traces, and reports; "
    "no consciousness, personhood, or agency claim is made.",
]


@dataclass
class CommunicationResponse:
    """One grounded response to the operator."""

    kind: str = "unknown"
    text: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    safety_status: str = "ok"
    governance_status: str = "ok"
    suggested_next_operator_action: Optional[str] = None
    claim_guard_safe: bool = True
    executed: bool = False
    response_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    timestamp: float = field(default_factory=time.time)
    # Optional LLM adapter markers (Prompt 20): a paraphrase changes
    # wording only; the deterministic content stays authoritative.
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def grounded(self) -> bool:
        return bool(self.evidence_refs) or bool(self.limitations)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "grounded": self.grounded}


@dataclass
class ResponseBuilder:
    """Renders, grounds, and scans every outgoing response."""

    responses_built: int = field(default=0, init=False)
    claim_guard_warnings: int = field(default=0, init=False)

    def _finish(self, response: CommunicationResponse,
                ) -> CommunicationResponse:
        from ..governance.compliance import ClaimGuard

        if not response.limitations:
            response.limitations = list(DEFAULT_LIMITATIONS)
        if not response.evidence_refs:
            response.limitations.append(
                "no direct evidence reference attaches to this response")
        guard = ClaimGuard()
        response.claim_guard_safe = guard.is_safe(response.text)
        if not response.claim_guard_safe:
            self.claim_guard_warnings += 1
            response.text = guard.rewrite(response.text)
            response.claim_guard_safe = guard.is_safe(response.text)
        self.responses_built += 1
        return response

    # -- response kinds ---------------------------------------------------------------

    def status_response(self, summary: str, evidence: List[str],
                        ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="status",
            text=render("status", summary=summary,
                        refs=", ".join(evidence) or "none recorded"),
            evidence_refs=list(evidence)))

    def health_response(self, summary: str, evidence: List[str],
                        ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="health",
            text=render("health", summary=summary,
                        refs=", ".join(evidence) or "none recorded"),
            evidence_refs=list(evidence)))

    def explanation_response(self, answer: str, evidence: List[str],
                             confidence: float = 0.0,
                             ) -> CommunicationResponse:
        response = CommunicationResponse(
            kind="explanation", text=render("explanation", answer=answer),
            evidence_refs=list(evidence))
        if confidence and confidence < 0.5:
            response.limitations = list(DEFAULT_LIMITATIONS) + [
                f"the underlying answer carries low confidence "
                f"({confidence:.2f})"]
        return self._finish(response)

    def report_response(self, path: str, claim_guard_safe: bool,
                        ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="report", executed=True,
            text=render("report", path=path,
                        claim_guard=claim_guard_safe),
            evidence_refs=[f"report:{path}"]))

    def governance_response(self, text: str, evidence: List[str],
                            executed: bool = True,
                            ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="governance", text=text, executed=executed,
            evidence_refs=list(evidence)))

    def confirmation_request(self, command_text: str,
                             confirmation_id: str,
                             ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="confirmation_request",
            text=render("confirmation_request", command=command_text,
                        confirmation_id=confirmation_id),
            evidence_refs=[f"pending_confirmation:{confirmation_id}"],
            suggested_next_operator_action=f"confirm {confirmation_id}"))

    def request_recorded_response(self, command_text: str, handler: str,
                                  evidence: List[str],
                                  ) -> CommunicationResponse:
        """The honest middle state: requested, recorded, not executed."""
        return self._finish(CommunicationResponse(
            kind="request_recorded", executed=False,
            text=render("request_recorded", command=command_text,
                        handler=handler),
            evidence_refs=list(evidence)))

    def rejection_response(self, reason: str,
                           suggested: Optional[str] = None,
                           ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="rejection", safety_status="refused",
            text=render("refused", reason=reason),
            evidence_refs=[f"refusal_reason:{reason[:80]}"],
            suggested_next_operator_action=suggested))

    def emergency_response(self, status: str, evidence: List[str],
                           ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="emergency", executed=True,
            text=render("emergency", status=status),
            evidence_refs=list(evidence)))

    def unsafe_response(self, reason: str) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="unsafe_refusal", safety_status="refused",
            text=render("refused", reason=reason),
            evidence_refs=[f"unsafe_pattern:{reason[:80]}"],
            suggested_next_operator_action="ask 'what can I ask?' for "
                                           "supported queries"))

    def unknown_response(self, examples: Optional[List[str]] = None,
                         ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="unknown",
            text=render("unknown", examples="; ".join(
                examples or ["status", "health", "show boundaries",
                             "why no action?", "generate report"])),
            suggested_next_operator_action="ask 'what can I ask?'"))

    def no_evidence_response(self) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="no_evidence", text=render("no_evidence")))

    def missing_component_response(self, component: str,
                                   ) -> CommunicationResponse:
        return self._finish(CommunicationResponse(
            kind="missing_component",
            text=render("missing_component", component=component)))

    def snapshot(self) -> Dict[str, Any]:
        return {"responses_built": self.responses_built,
                "claim_guard_warnings": self.claim_guard_warnings,
                "note": "every response is templated, grounded, and "
                        "ClaimGuard-scanned"}
