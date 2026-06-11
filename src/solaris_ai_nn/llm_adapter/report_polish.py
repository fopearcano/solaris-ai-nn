"""Report polisher -- wording may change; structure and facts may not.

A polished Markdown report must keep every heading, every number, every
warning line, and the limitations section. The structural checks run
*after* the model returns: any heading dropped, any metric changed, any
warning removed, and the polish is rejected in favor of the raw report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .audit import LLMAuditLog
from .base import LLMAdapter, LLMRequest, LLMTaskType
from .claim_filter import LLMClaimFilter
from .grounding import GroundingValidator

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_STRENGTHENERS = ("definitely", "certainly", "proves", "guarantees",
                  "always succeeds", "fully understands")


def _headings(markdown: str) -> List[str]:
    return [line.strip() for line in markdown.splitlines()
            if line.strip().startswith("#")]


def _warning_lines(markdown: str) -> List[str]:
    return [line.strip() for line in markdown.splitlines()
            if any(word in line.lower()
                   for word in ("warning", "incident", "violation",
                                "unsafe"))]


@dataclass
class PolishResult:
    """The outcome: polished text or the raw original, with reasons."""

    text: str = ""
    accepted: bool = False
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ReportPolisher:
    """Polish-or-fallback for Markdown reports."""

    adapter: LLMAdapter
    validator: GroundingValidator = field(
        default_factory=GroundingValidator)
    claim_filter: LLMClaimFilter = field(default_factory=LLMClaimFilter)
    audit: Optional[LLMAuditLog] = None
    accepted_count: int = field(default=0, init=False)
    rejected_count: int = field(default=0, init=False)

    def polish_markdown(self, markdown: str,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> PolishResult:
        raw = str(markdown)
        request = LLMRequest(
            task_type=LLMTaskType.REPORT_POLISH, input_text=raw,
            allowed_facts=[raw[:4000]],
            grounded_context=dict(context or {}))
        response = self.adapter.generate(request)
        result = PolishResult(text=raw, accepted=False)
        verdicts: Dict[str, Any] = {"grounding": None,
                                    "claim_guard": None}
        try:
            if response.refused:
                result.reasons.append(response.refusal_reason)
                return result
            polished = response.output_text
            result.reasons.extend(self._structural_violations(raw,
                                                              polished))
            if result.reasons:
                self.rejected_count += 1
                return result
            grounding = self.validator.validate(request, response)
            verdicts["grounding"] = grounding.passed
            if not grounding.passed:
                result.reasons.extend(grounding.violations)
                self.rejected_count += 1
                return result
            ok, safe_text = self.claim_filter.enforce(polished)
            verdicts["claim_guard"] = ok
            if not ok:
                result.reasons.append("ClaimGuard rejected the polished "
                                      "text")
                self.rejected_count += 1
                return result
            self.accepted_count += 1
            result.text = safe_text
            result.accepted = True
            return result
        finally:
            if self.audit is not None:
                self.audit.record(
                    request=request, response=response,
                    grounding_passed=verdicts.get("grounding"),
                    claim_guard_passed=verdicts.get("claim_guard"),
                    fallback_used=not result.accepted,
                    adapter_type=self.adapter.name,
                    safety_decision="accepted" if result.accepted
                    else "rejected")

    @staticmethod
    def _structural_violations(raw: str, polished: str) -> List[str]:
        violations: List[str] = []
        for heading in _headings(raw):
            if heading not in polished:
                violations.append(f"heading dropped: {heading!r}")
        raw_numbers = sorted(_NUMBER_RE.findall(raw))
        polished_numbers = sorted(_NUMBER_RE.findall(polished))
        if raw_numbers != polished_numbers:
            violations.append("metric numbers changed or went missing")
        for warning in _warning_lines(raw):
            if warning not in polished:
                violations.append(f"warning/incident line removed: "
                                  f"{warning[:60]!r}")
        if "limitation" in raw.lower() \
                and "limitation" not in polished.lower():
            violations.append("the limitations section was removed")
        lowered = polished.lower()
        for strengthener in _STRENGTHENERS:
            if strengthener in lowered and strengthener not in raw.lower():
                violations.append(f"claims made stronger: "
                                  f"{strengthener!r} introduced")
        return violations

    def snapshot(self) -> Dict[str, Any]:
        return {
            "adapter": self.adapter.name,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "note": "wording may change; headings, numbers, warnings, "
                    "and limitations may not",
        }
