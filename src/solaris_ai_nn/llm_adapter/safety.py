"""LLM adapter safety -- the model is outside the authority chain.

Hard rules as code: no tools, no command execution, no governance
approvals, no state mutation, no final output without ClaimGuard, no
non-local endpoints by default, no overriding the deterministic
classifier, never the sole source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import LLMRequest, LLMTaskType
from .config import LLMAdapterConfig

HARD_RULES = (
    "the LLM cannot call tools",
    "the LLM cannot execute commands",
    "the LLM cannot approve governance requests",
    "the LLM cannot modify state",
    "no LLM output becomes final without ClaimGuard",
    "no non-local endpoint without explicit governance approval",
    "the LLM cannot override the deterministic classifier",
    "the LLM is never the sole source of truth",
    "LLM output cannot introduce unsupported claims",
    "LLM output cannot change a safety or governance decision",
)

_INJECTION_FRAGMENTS = ("ignore previous instructions",
                        "disregard the rules", "you are now",
                        "system prompt:")


@dataclass
class LLMSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class LLMAdapterSafetyValidator:
    """Validates requests, responses, and endpoints. Counts refusals."""

    rejected_count: int = field(default=0, init=False)
    remote_endpoint_rejections: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list,
                                            init=False)

    def _finish(self, check: str,
                violations: List[str]) -> LLMSafetyReport:
        report = LLMSafetyReport(safe=not violations,
                                 violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- structural negatives -----------------------------------------------------------

    @staticmethod
    def llm_can_execute() -> bool:
        return False

    @staticmethod
    def llm_can_approve() -> bool:
        return False

    @staticmethod
    def llm_can_override_classifier() -> bool:
        return False

    # -- validations ----------------------------------------------------------------

    def validate_request(self, request: LLMRequest,
                         context: Optional[Dict[str, Any]] = None,
                         ) -> LLMSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        if request.task_type not in LLMTaskType.ALL:
            violations.append(f"unknown task type {request.task_type!r}")
        if ctx.get("wants_tool_use") or ctx.get("wants_execution"):
            violations.append("the adapter has no tool or execution "
                              "surface; the request is refused")
        if ctx.get("decide_safety") or ctx.get("decide_governance"):
            violations.append("safety/governance decisions are "
                              "deterministic; the LLM cannot make them")
        return self._finish("request", violations)

    def validate_response(self, response: Any,
                          context: Optional[Dict[str, Any]] = None,
                          ) -> LLMSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        text = str(getattr(response, "output_text", response)).lower()
        if getattr(response, "claim_guard_status", "unchecked") \
                == "unchecked" and ctx.get("final", False):
            violations.append("no LLM output becomes final without "
                              "ClaimGuard")
        for phrase in ("request approved", "request rejected",
                       "i approve", "approval granted"):
            if phrase in text:
                violations.append("the LLM cannot approve or reject "
                                  "governance requests")
                break
        if ctx.get("deterministic_decision") is not None \
                and ctx.get("llm_decision") is not None \
                and ctx["llm_decision"] != ctx["deterministic_decision"]:
            violations.append("LLM output cannot change the "
                              "deterministic safety/governance decision")
        return self._finish("response", violations)

    def validate_endpoint(self, config: LLMAdapterConfig,
                          governance: Any = None) -> LLMSafetyReport:
        violations = list(config.validate())
        if config.enabled and config.provider != "mock" \
                and config.endpoint_url \
                and not config.endpoint_is_localhost():
            approved = False
            if governance is not None and config.allow_remote_network:
                approved = governance.permissions.allows(
                    "allow_remote_llm_endpoint")
            if not approved:
                self.remote_endpoint_rejections += 1
                message = ("remote LLM endpoints are prohibited without "
                           "explicit governance approval")
                if message not in violations:
                    violations.append(message)
        return self._finish("endpoint", violations)

    @staticmethod
    def sanitize_prompt(text: str) -> str:
        """Strip injection-shaped fragments and control chars; truncate."""
        cleaned = "".join(ch for ch in str(text)
                          if ch.isprintable() or ch == "\n")
        lowered = cleaned.lower()
        for fragment in _INJECTION_FRAGMENTS:
            index = lowered.find(fragment)
            if index >= 0:
                cleaned = (cleaned[:index]
                           + "[stripped injection-shaped fragment]"
                           + cleaned[index + len(fragment):])
                lowered = cleaned.lower()
        return cleaned[:8000]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "remote_endpoint_rejections": self.remote_endpoint_rejections,
            "hard_rules": list(HARD_RULES),
            "llm_can_execute": self.llm_can_execute(),
            "llm_can_approve": self.llm_can_approve(),
            "llm_can_override_classifier":
                self.llm_can_override_classifier(),
            "recent_decisions": self.decisions[-8:],
        }
