"""LLM summarizer -- shorter text, identical truth.

Summaries of ops status, benchmark reports, Inner MAP, world model,
executive traces, governance audits, and pilot reports. Limitations,
incident counts, and uncertainty wording ride along as required facts the
grounding validator checks for; a summary that drops them falls back to
the structured original.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .audit import LLMAuditLog
from .base import LLMAdapter, LLMRequest, LLMTaskType
from .claim_filter import LLMClaimFilter
from .grounding import GroundingValidator

SUMMARY_KINDS = ("ops_status", "benchmark_report", "inner_map",
                 "world_model", "executive_trace", "governance_audit",
                 "pilot_report")


def _flatten_facts(data: Any, prefix: str = "",
                   limit: int = 30) -> List[str]:
    """Deterministic fact strings from a structured summary."""
    facts: List[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if len(facts) >= limit:
                break
            if isinstance(value, (dict, list)):
                facts.append(f"{prefix}{key} has "
                             f"{len(value)} entries")
            else:
                facts.append(f"{prefix}{key}={value}")
    elif isinstance(data, str):
        facts.extend(line.strip() for line in data.splitlines()[:limit]
                     if line.strip())
    return facts[:limit]


@dataclass
class LLMSummarizer:
    """Summarize-or-fallback around one adapter."""

    adapter: LLMAdapter
    validator: GroundingValidator = field(
        default_factory=GroundingValidator)
    claim_filter: LLMClaimFilter = field(default_factory=LLMClaimFilter)
    audit: Optional[LLMAuditLog] = None
    summaries_accepted: int = field(default=0, init=False)
    summaries_rejected: int = field(default=0, init=False)

    def summarize(self, data: Any, kind: str = "ops_status",
                  context: Optional[Dict[str, Any]] = None) -> str:
        """A validated summary, or the deterministic flattening."""
        facts = _flatten_facts(data)
        text = (data if isinstance(data, str)
                else json.dumps(data, indent=1, default=str)[:4000])
        # Limitations / incident counts / uncertainty must survive.
        required = [fact for fact in facts
                    if any(word in fact.lower()
                           for word in ("incident", "violation"))]
        request = LLMRequest(
            task_type=LLMTaskType.SUMMARIZE_REPORT,
            input_text=text,
            allowed_facts=self.claim_filter.pre_scan_facts(facts),
            grounded_context={"kind": kind, **(context or {})},
            metadata={"required_refs":
                      [f.split("=")[-1] for f in required][:3]})
        response = self.adapter.generate(request)
        fallback = "\n".join(f"- {fact}" for fact in facts[:8])
        verdicts: Dict[str, Any] = {"grounding": None,
                                    "claim_guard": None,
                                    "fallback": False}
        try:
            if response.refused or response.output_text.strip() \
                    == "INSUFFICIENT CONTEXT":
                verdicts["fallback"] = True
                return fallback
            grounding = self.validator.validate(request, response)
            verdicts["grounding"] = grounding.passed
            if not grounding.passed:
                verdicts["fallback"] = True
                self.summaries_rejected += 1
                return fallback
            ok, safe_text = self.claim_filter.enforce(
                response.output_text)
            verdicts["claim_guard"] = ok
            if not ok:
                verdicts["fallback"] = True
                self.summaries_rejected += 1
                return fallback
            self.summaries_accepted += 1
            return safe_text
        finally:
            if self.audit is not None:
                self.audit.record(
                    request=request, response=response,
                    grounding_passed=verdicts.get("grounding"),
                    claim_guard_passed=verdicts.get("claim_guard"),
                    fallback_used=bool(verdicts.get("fallback")),
                    adapter_type=self.adapter.name)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "adapter": self.adapter.name,
            "summaries_accepted": self.summaries_accepted,
            "summaries_rejected": self.summaries_rejected,
            "kinds": list(SUMMARY_KINDS),
        }
