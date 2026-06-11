"""LLM paraphraser -- readability for already-safe text, or nothing.

The deterministic response always exists first. The paraphraser builds a
request whose allowed facts are exactly that response (plus its evidence),
calls the adapter, validates grounding, runs ClaimGuard, and only then
swaps the wording. Any failure at any stage returns the deterministic
original untouched -- fallback is mandatory, not optional.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .audit import LLMAuditLog
from .base import LLMAdapter, LLMRequest, LLMTaskType
from .claim_filter import LLMClaimFilter
from .grounding import GroundingValidator


@dataclass
class LLMParaphraser:
    """Paraphrase-or-fallback around one adapter."""

    adapter: LLMAdapter
    validator: GroundingValidator = field(
        default_factory=GroundingValidator)
    claim_filter: LLMClaimFilter = field(default_factory=LLMClaimFilter)
    audit: Optional[LLMAuditLog] = None
    accepted_count: int = field(default=0, init=False)
    rejected_count: int = field(default=0, init=False)
    fallback_count: int = field(default=0, init=False)

    # -- core pipeline ------------------------------------------------------------------

    def _paraphrase_text(self, text: str, evidence: Any = None,
                         context: Optional[Dict[str, Any]] = None,
                         task_type: str =
                         LLMTaskType.PARAPHRASE_RESPONSE,
                         ) -> "tuple[Optional[str], Dict[str, Any]]":
        """(paraphrased_or_None, verdicts). None means: keep original."""
        ctx = dict(context or {})
        facts = self.claim_filter.pre_scan_facts(
            [text] + [str(ref) for ref in (evidence or [])])
        request = LLMRequest(
            task_type=task_type, input_text=str(text),
            allowed_facts=facts, grounded_context=ctx,
            metadata={"required_refs": list(evidence or [])[:5]})
        response = self.adapter.generate(request)
        verdicts: Dict[str, Any] = {"grounding": None, "claim_guard": None,
                                    "fallback": False}
        if response.refused \
                or response.output_text.strip() == "INSUFFICIENT CONTEXT":
            verdicts["fallback"] = True
            self.fallback_count += 1
            self._record(request, response, verdicts)
            return (None, verdicts)
        grounding = self.validator.validate(request, response)
        verdicts["grounding"] = grounding.passed
        if not grounding.passed:
            verdicts["fallback"] = True
            self.rejected_count += 1
            self.fallback_count += 1
            self._record(request, response, verdicts)
            return (None, verdicts)
        ok, safe_text = self.claim_filter.enforce(response.output_text)
        verdicts["claim_guard"] = ok
        response.claim_guard_status = "safe" if ok else "unsafe"
        if not ok:
            verdicts["fallback"] = True
            self.rejected_count += 1
            self.fallback_count += 1
            self._record(request, response, verdicts)
            return (None, verdicts)
        self.accepted_count += 1
        self._record(request, response, verdicts)
        return (safe_text, verdicts)

    def _record(self, request: LLMRequest, response: Any,
                verdicts: Dict[str, Any]) -> None:
        if self.audit is not None:
            self.audit.record(
                request=request, response=response,
                grounding_passed=verdicts.get("grounding"),
                claim_guard_passed=verdicts.get("claim_guard"),
                fallback_used=bool(verdicts.get("fallback")),
                adapter_type=self.adapter.name,
                safety_decision="fallback" if verdicts.get("fallback")
                else "accepted")

    # -- public API ---------------------------------------------------------------------

    def paraphrase_response(self, response: Any,
                            context: Optional[Dict[str, Any]] = None,
                            ) -> Any:
        """Paraphrase a CommunicationResponse-like object, or return it."""
        text = getattr(response, "text", None)
        if not text:
            return response
        evidence = list(getattr(response, "evidence_refs", []) or [])
        paraphrased, verdicts = self._paraphrase_text(text, evidence,
                                                      context)
        if paraphrased is None:
            if hasattr(response, "limitations"):
                response.limitations = list(response.limitations)
            return response
        response.text = paraphrased
        if hasattr(response, "limitations"):
            response.limitations = list(response.limitations) + [
                "this wording is an LLM paraphrase of a deterministic "
                "response; the deterministic content is authoritative"]
        metadata = getattr(response, "metadata", None)
        if isinstance(metadata, dict):
            metadata["llm_paraphrased"] = True
        else:
            try:
                response.metadata = {"llm_paraphrased": True}
            except AttributeError:
                pass
        return response

    def paraphrase_explanation(self, explanation: str,
                               context: Optional[Dict[str, Any]] = None,
                               ) -> str:
        paraphrased, _ = self._paraphrase_text(explanation,
                                               context=context)
        return paraphrased if paraphrased is not None else str(explanation)

    def paraphrase_report_section(self, section: str,
                                  context: Optional[Dict[str, Any]] =
                                  None) -> str:
        paraphrased, _ = self._paraphrase_text(
            section, context=context,
            task_type=LLMTaskType.REPORT_POLISH)
        return paraphrased if paraphrased is not None else str(section)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "adapter": self.adapter.name,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "fallback_count": self.fallback_count,
            "grounding": self.validator.snapshot(),
            "claim_filter": self.claim_filter.snapshot(),
        }
