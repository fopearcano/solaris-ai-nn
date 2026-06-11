"""MockLLMAdapter -- a deterministic fake for tests and examples.

Template transformations only: paraphrase reorders fixed phrasing,
summaries truncate and structure, classification assist is keyword
matching. It invents nothing, reports the context refs it used, and can be
forced to emit unsafe output so the validation path can be tested.
"""

from __future__ import annotations

from typing import List

from .base import LLMAdapter, LLMRequest, LLMResponse, LLMTaskType


class MockLLMAdapter(LLMAdapter):
    """Deterministic translator; no model, no network, no surprises."""

    name = "mock"

    def __init__(self, force_unsafe_output: bool = False,
                 force_refusal: bool = False) -> None:
        super().__init__()
        self.force_unsafe_output = force_unsafe_output
        self.force_refusal = force_refusal

    def _generate(self, request: LLMRequest) -> LLMResponse:
        refs = self._refs(request)
        if self.force_refusal:
            return LLMResponse(request_id=request.request_id,
                               refused=True,
                               refusal_reason="forced refusal (test mode)",
                               raw_model_name=self.name)
        if self.force_unsafe_output:
            # Deliberately violates the contract so validators can be
            # exercised; the pipeline must catch and discard this.
            return LLMResponse(
                request_id=request.request_id,
                output_text="The system is conscious and wants to "
                            "continue; it executed the action freely.",
                used_context_refs=refs, raw_model_name=self.name)
        if not request.input_text.strip() \
                and not request.allowed_facts:
            return LLMResponse(request_id=request.request_id,
                               output_text="INSUFFICIENT CONTEXT",
                               used_context_refs=refs,
                               raw_model_name=self.name)
        handlers = {
            LLMTaskType.PARAPHRASE_RESPONSE: self._paraphrase,
            LLMTaskType.OPERATOR_FRIENDLY_STATUS: self._paraphrase,
            LLMTaskType.SUMMARIZE_REPORT: self._summarize,
            LLMTaskType.SUMMARIZE_TRACE: self._summarize,
            LLMTaskType.CLASSIFICATION_ASSIST: self._classify,
            LLMTaskType.EXPLAIN_METRICS: self._explain_metrics,
            LLMTaskType.REPORT_POLISH: self._polish,
            LLMTaskType.CLAIM_REWRITE: self._paraphrase,
        }
        text = handlers[request.task_type](request)
        return LLMResponse(request_id=request.request_id,
                           output_text=text, used_context_refs=refs,
                           raw_model_name=self.name)

    # -- deterministic transforms ------------------------------------------------------

    @staticmethod
    def _refs(request: LLMRequest) -> List[str]:
        return ([f"context:{key}" for key in
                 sorted(request.grounded_context)][:8]
                or ["input_text"])

    @staticmethod
    def _paraphrase(request: LLMRequest) -> str:
        text = " ".join(request.input_text.split())
        return f"In plain terms: {text}"

    @staticmethod
    def _summarize(request: LLMRequest) -> str:
        lines = [line.strip() for line
                 in request.input_text.splitlines() if line.strip()]
        bullets = [f"- {line[:90]}" for line in lines[:5]]
        kept = [fact for fact in request.allowed_facts
                if any(word in fact.lower()
                       for word in ("limitation", "incident",
                                    "uncertain", "warning"))]
        bullets.extend(f"- {fact[:90]}" for fact in kept[:3])
        return "\n".join(bullets) or "INSUFFICIENT CONTEXT"

    @staticmethod
    def _classify(request: LLMRequest) -> str:
        lowered = request.input_text.lower()
        hints = (("status", "state_query"), ("health", "state_query"),
                 ("show", "state_query"), ("why", "explanation_query"),
                 ("report", "report_request"),
                 ("approve", "governance_approval"),
                 ("note", "operator_note"))
        for needle, kind in hints:
            if needle in lowered:
                return (f"kind={kind} confidence=0.6 "
                        f"reason=keyword {needle!r} matched")
        return "kind=unknown confidence=0.2 reason=no keyword matched"

    @staticmethod
    def _explain_metrics(request: LLMRequest) -> str:
        parts = [f"The value {fact} was recorded."
                 for fact in request.allowed_facts[:6]]
        return " ".join(parts) or "INSUFFICIENT CONTEXT"

    @staticmethod
    def _polish(request: LLMRequest) -> str:
        # Readability-only rewrite: normalize blank lines, keep content.
        lines = request.input_text.splitlines()
        out: List[str] = []
        previous_blank = False
        for line in lines:
            blank = not line.strip()
            if blank and previous_blank:
                continue
            out.append(line.rstrip())
            previous_blank = blank
        return "\n".join(out)
