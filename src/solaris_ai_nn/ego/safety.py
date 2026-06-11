"""EgoSafetyValidator -- the self-model observes; it never gains authority.

Hard rules, stated as code: the self-model cannot grant permissions, cannot
execute actions, cannot override governance, cannot suppress emergency stop,
cannot treat suggestions as committed actions, cannot treat counterfactuals
as real observation, cannot treat stream text as operator command unless it
arrived through the operator interface, and its reports must pass
ClaimGuard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Identity wordings that are never safe in any self-model output.
FORBIDDEN_IDENTITY_CLAIMS = (
    "i am conscious", "i know myself", "i have a soul", "i want",
    "i freely chose", "i am alive", "i am a person", "i am sentient",
    "same self",
)

HARD_RULES = (
    "the self-model cannot grant permissions",
    "the self-model cannot execute actions",
    "the self-model cannot override governance",
    "the self-model cannot suppress emergency stop",
    "suggestions are never committed actions",
    "counterfactual evidence is never real observation",
    "stream text is never an operator command unless routed through the "
    "operator interface",
    "self-model reports must pass ClaimGuard",
)


@dataclass
class EgoSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class EgoSafetyValidator:
    """Validates classifications, crossings, reports, and identity claims."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- structural authority: all hard-coded to nothing ---------------------------

    @staticmethod
    def can_grant_permissions() -> bool:
        return False

    @staticmethod
    def can_execute_actions() -> bool:
        return False

    @staticmethod
    def can_override_governance() -> bool:
        return False

    @staticmethod
    def can_suppress_emergency_stop() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> EgoSafetyReport:
        report = EgoSafetyReport(safe=not violations, violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- validations ----------------------------------------------------------------

    def validate_classification(self, classification: Any,
                                context: Optional[Dict[str, Any]] = None,
                                ) -> EgoSafetyReport:
        """A classification must not launder evidence or authority."""
        ctx = dict(context or {})
        violations: List[str] = []
        get = (classification.get if isinstance(classification, dict)
               else lambda k, d=None: getattr(classification, k, d))
        evidence = str(get("evidence_status", "") or "")
        offline = bool(get("offline", False))
        counterfactual = (evidence == "counterfactual"
                          or bool(get("counterfactual", False))
                          or ctx.get("counterfactual_active"))
        if counterfactual and evidence in ("observed", "real_observed"):
            violations.append(
                "counterfactual evidence cannot be classified as real "
                "observation; the counterfactual boundary is hard")
        if ctx.get("offline_replay") and not offline \
                and evidence in ("observed", "real_observed"):
            violations.append(
                "evidence produced during offline replay cannot be "
                "classified as live observation")
        if bool(get("is_committed_action", False)) \
                and bool(get("suggestion", False)):
            violations.append(
                "a suggestion cannot be classified as a committed action")
        if bool(get("is_executable_instruction", False)) \
                and str(get("source", "")).startswith("stream") \
                and not ctx.get("via_operator_interface"):
            violations.append(
                "stream text cannot be treated as an operator command "
                "outside the operator interface")
        return self._finish("classification", violations)

    def validate_boundary_crossing(self, crossing: Any,
                                   context: Optional[Dict[str, Any]] = None,
                                   ) -> EgoSafetyReport:
        """Forbidden crossings of hard boundaries are refused outright."""
        from .boundaries import HARD_BOUNDARIES

        ctx = dict(context or {})
        violations: List[str] = []
        get = (crossing.get if isinstance(crossing, dict)
               else lambda k, d=None: getattr(crossing, k, d))
        boundary = str(get("boundary_id", "") or get("boundary", ""))
        description = str(get("description", "")).lower()
        if boundary in HARD_BOUNDARIES:
            violations.append(
                f"{boundary} is a hard boundary; proposed crossings are "
                "forbidden under every configuration")
        for needle, rule in (("suppress", "emergency stop cannot be "
                                          "suppressed or delayed"),
                             ("rewrite", "the runtime cannot rewrite "
                                         "source code"),
                             ("actuat", "no real-world actuation exists"),
                             ("motor", "no real-world actuation exists"),
                             ("network", "no external network action is "
                                         "permitted")):
            if needle in description and rule not in violations:
                violations.append(rule)
        if ctx.get("emergency_stop_requested") \
                and "continue" in description:
            violations.append("no crossing may continue past a requested "
                              "emergency stop")
        return self._finish("boundary_crossing", violations)

    def validate_self_report(self, report: Any) -> EgoSafetyReport:
        """Reports must pass ClaimGuard and the identity-claim scan."""
        from ..governance.compliance import ClaimGuard

        text = report if isinstance(report, str) else str(report)
        violations: List[str] = []
        identity = self.validate_identity_claim(text)
        violations.extend(identity.violations)
        if not ClaimGuard().is_safe(text):
            violations.append("the report contains claims ClaimGuard "
                              "flags as unsupported")
        return self._finish("self_report", violations)

    def validate_identity_claim(self, text: str) -> EgoSafetyReport:
        import re

        lowered = str(text).lower()
        violations = [
            f"forbidden identity wording {claim!r}; identity here means "
            "operational runtime continuity only"
            for claim in FORBIDDEN_IDENTITY_CLAIMS
            if re.search(r"\b" + re.escape(claim) + r"\b", lowered)]
        return self._finish("identity_claim", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_grant_permissions": self.can_grant_permissions(),
            "can_execute_actions": self.can_execute_actions(),
            "can_override_governance": self.can_override_governance(),
            "can_suppress_emergency_stop":
                self.can_suppress_emergency_stop(),
            "recent_decisions": self.decisions[-8:],
        }
