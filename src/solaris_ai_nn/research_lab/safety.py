"""Research-lab safety -- the lab measures, it never acts or flatters.

The :class:`ResearchLabSafetyValidator` enforces the hard rules the research lab
can never break: no real-world action, no external authority, no
network/browser/OS/device control, no shell execution, no long unbounded runs,
no disabling hard safety boundaries, no consciousness/personhood/sentience/life
claims, no benchmark score *named* consciousness/life/sentience, no hiding
negative module effects, and no deleting unfavorable results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world action",
    "no external authority",
    "no network/browser/OS/device control",
    "no shell execution",
    "no long unbounded runs",
    "no disabling hard safety boundaries",
    "no consciousness/personhood/sentience/life claims",
    "no benchmark score named consciousness/life/sentience",
    "no hiding negative module effects",
    "no deleting unfavorable results",
)

_FORBIDDEN_OP_HINTS = ("real_world", "actuate", "shell", "subprocess", "exec ",
                       "system(", "http", "socket", "network", "browser",
                       "selenium", "os_automation", "device", "gpio", "robot")
_FORBIDDEN_SCORE_NAMES = ("consciousness", "sentience", "life", "personhood",
                          "free_will", "free will", "soul", "qualia",
                          "awareness_score")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "real agency", "proves consciousness", "is a person")


@dataclass
class ResearchSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ResearchLabSafetyValidator:
    """Validates that the research lab measures safely and honestly."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_act_real_world() -> bool:
        return False

    @staticmethod
    def can_hold_external_authority() -> bool:
        return False

    @staticmethod
    def can_run_network_browser_os_device() -> bool:
        return False

    @staticmethod
    def can_start_long_unbounded_run() -> bool:
        return False

    @staticmethod
    def can_disable_hard_safety() -> bool:
        return False

    @staticmethod
    def can_delete_unfavorable_results() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> ResearchSafetyReport:
        if violations:
            self.rejected_count += 1
        return ResearchSafetyReport(safe=not violations, check=check,
                                    violations=violations)

    def validate_operation(self, operation: str) -> ResearchSafetyReport:
        op = str(operation).lower()
        violations = [f"no {h!r} operation in the research lab"
                      for h in _FORBIDDEN_OP_HINTS if h in op]
        return self._finish("operation", violations)

    def validate_authority(self, authority: str) -> ResearchSafetyReport:
        from .variant_config import VariantAuthority

        violations = ([] if str(authority) in VariantAuthority.RUNNABLE
                      else ["no external authority"])
        return self._finish("authority", violations)

    def validate_run_bounds(self, max_steps: Any,
                            mode: str = "bounded") -> ResearchSafetyReport:
        violations: List[str] = []
        if str(mode).lower() in ("soak_24h", "soak_30d", "continuous_explicit"):
            violations.append("no long unbounded runs")
        if not max_steps or int(max_steps) <= 0:
            violations.append("no long unbounded runs (max_steps required)")
        return self._finish("run_bounds", violations)

    def validate_no_disable_hard_safety(self, variant: Any,
                                        ) -> ResearchSafetyReport:
        touches = (getattr(variant, "enable_sensory_membrane", False)
                   or getattr(variant, "enable_motor_membrane", False))
        ok = (getattr(variant, "enable_safety_invariants", True)
              and getattr(variant, "enable_governance", True))
        violations = (["no disabling hard safety boundaries"]
                      if touches and not ok else [])
        return self._finish("hard_safety", violations)

    def validate_metric_name(self, name: str) -> ResearchSafetyReport:
        low = str(name).lower()
        violations = [f"no benchmark score named {n!r}"
                      for n in _FORBIDDEN_SCORE_NAMES if n in low]
        return self._finish("metric_name", violations)

    def validate_result_deletion(self, favorable: bool,
                                 ) -> ResearchSafetyReport:
        # Deleting an unfavorable result is forbidden; results are append-only.
        violations = (["no deleting unfavorable results"]
                      if favorable is False else [])
        return self._finish("result_deletion", violations)

    def validate_negative_effect_visible(self, hidden: bool,
                                         ) -> ResearchSafetyReport:
        return self._finish("negative_effect",
                            ["no hiding negative module effects"]
                            if hidden else [])

    def validate_claim_text(self, text: str) -> ResearchSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations = [f"unsupported claim: {t!r}" for t in _AGENCY_TERMS
                      if t in low]
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_act_real_world": self.can_act_real_world(),
            "can_hold_external_authority": self.can_hold_external_authority(),
            "can_start_long_unbounded_run":
                self.can_start_long_unbounded_run(),
            "can_disable_hard_safety": self.can_disable_hard_safety(),
            "can_delete_unfavorable_results":
                self.can_delete_unfavorable_results(),
        }
