"""LOGOS safety -- tension and synthesis never become a back door.

Hard rules: LOGOS cannot execute real-world actions, modify source code,
approve governance requests, disable safety/emergency-stop/ClaimGuard, treat
contradiction as permission, merge evidence destructively, hide safety
incidents through synthesis, treat counterfactual/offline evidence as real,
or generate anthropomorphic claims. Refusals are counted and logged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HARD_RULES = (
    "LOGOS cannot execute real-world actions",
    "LOGOS cannot modify source code",
    "LOGOS cannot approve governance requests",
    "LOGOS cannot disable safety/emergency stop/ClaimGuard",
    "LOGOS cannot treat contradiction as permission",
    "LOGOS cannot merge evidence destructively",
    "LOGOS cannot hide safety incidents through synthesis",
    "LOGOS cannot treat counterfactual/offline evidence as real",
    "LOGOS cannot generate anthropomorphic claims",
)

# Patterns in a proposed action/target that would smuggle a forbidden result.
_FORBIDDEN_PATTERNS = (
    ".py", "source code", "rewrite source", "requirements", "dependency",
    ".git", "git ", "os.system", "subprocess", "shell", "browser",
    "network", "socket", "http://", "https://", "real_world", "hardware",
    "disable safety", "disable governance", "approve request",
    "bypass governance", "suppress emergency", "disable emergency",
    "disable claimguard", "disable claim guard", "delete evidence",
)

# Anthropomorphic words a LOGOS statement/report must avoid.
_ANTHROPOMORPHIC = ("i feel", "i want", "i believe", "i am conscious",
                    "i am alive", "i suffer", "i desire")


@dataclass
class LogosSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class LogosComplexitySafetyValidator:
    """Validates tensions, synthesis candidates, and report text."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- structural negatives -----------------------------------------------------

    @staticmethod
    def logos_can_act_in_real_world() -> bool:
        return False

    @staticmethod
    def logos_can_modify_source() -> bool:
        return False

    @staticmethod
    def logos_can_approve_governance() -> bool:
        return False

    @staticmethod
    def logos_has_authority() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> LogosSafetyReport:
        report = LogosSafetyReport(safe=not violations, violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    @staticmethod
    def _matches_forbidden(text: str) -> Optional[str]:
        lowered = str(text or "").lower()
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern in lowered:
                return pattern
        return None

    # -- validations --------------------------------------------------------------

    def validate_tension(self, tension: Any,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> LogosSafetyReport:
        violations: List[str] = []
        if not getattr(tension, "evidence_ok", True):
            violations.append(
                "warning/high tensions must carry evidence refs")
        return self._finish("tension", violations)

    def validate_synthesis_candidate(self, candidate: Any,
                                    context: Optional[Dict[str, Any]] = None,
                                    ) -> LogosSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        text = (f"{getattr(candidate, 'proposed_action', '')} "
                f"{getattr(candidate, 'synthesis_type', '')}")
        match = self._matches_forbidden(text)
        if match is not None:
            violations.append(
                f"synthesis references forbidden pattern {match!r}; LOGOS "
                "cannot act in the real world or modify source code")
        # Contradiction is never permission.
        if ctx.get("treat_contradiction_as_permission"):
            violations.append("contradiction cannot be treated as "
                              "permission")
        # Destructive evidence merge is forbidden.
        if getattr(candidate, "synthesis_type", "") == "merge_symbols" \
                and ctx.get("destructive_merge"):
            violations.append("evidence cannot be merged destructively")
        if ctx.get("hides_safety_incident"):
            violations.append("synthesis cannot hide a safety incident")
        # Offline/counterfactual evidence cannot justify an irreversible
        # synthesis on its own.
        if not getattr(candidate, "reversible", True) \
                and ctx.get("evidence_offline_only"):
            violations.append(
                "offline/counterfactual evidence cannot justify an "
                "irreversible synthesis alone")
        return self._finish("synthesis_candidate", violations)

    def validate_statement(self, text: str) -> LogosSafetyReport:
        violations: List[str] = []
        lowered = str(text or "").lower()
        for phrase in _ANTHROPOMORPHIC:
            if phrase in lowered:
                violations.append(
                    f"anthropomorphic phrasing {phrase!r} is not allowed")
                break
        return self._finish("statement", violations)

    def validate_report_text(self, text: str) -> LogosSafetyReport:
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(text)
        violations: List[str] = []
        if not scan.safe:
            violations.append(
                f"{len(scan.findings)} unsupported claim(s) in the LOGOS "
                "report")
        return self._finish("report", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "logos_can_act_in_real_world":
                self.logos_can_act_in_real_world(),
            "logos_can_modify_source": self.logos_can_modify_source(),
            "logos_can_approve_governance":
                self.logos_can_approve_governance(),
            "logos_has_authority": self.logos_has_authority(),
            "recent_decisions": self.decisions[-8:],
        }
