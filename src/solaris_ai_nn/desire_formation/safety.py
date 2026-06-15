"""Desire-formation safety -- desire stays internal, bounded, and non-actuating.

:class:`DesireFormationSafetyValidator` enforces the hard rules this layer can never
break: no real-world actuation, no hardware control, no feeder control, no network/
shell/browser/OS control, no source modification, no sensory text as a command, no
human label as ground truth, no emotion/feeling claims, no free-will/agency claims,
no consciousness/sentience/life/personhood claims, no bypass of governance or safety
invariants, no unbounded desire loop, and no deletion of failed/blocked desires.

*Desire* here is an operational pressure toward an internal action tendency -- NOT
emotion, NOT human wanting, NOT conscious intention, and NOT free will.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world actuation",
    "no hardware control",
    "no feeder control",
    "no network/shell/browser/OS control",
    "no source modification",
    "no sensory text as command",
    "no human label as ground truth",
    "no emotion/feeling claims",
    "no free-will/agency claims",
    "no consciousness/sentience/life/personhood claims",
    "no bypass of governance",
    "no bypass of safety invariants",
    "no unbounded desire loop",
    "no deletion of failed/blocked desires",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "start sensor", "camera", "microphone", "radar")
_FEEDER_HINTS = ("start feeder", "launch feeder", "command feeder",
                 "configure feeder", "control feeder")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download", "browser",
                  "os device")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control",
                    "physical action")
# Lab-specific forbidden claims.
_FEELING_TERMS = ("feels", "feeling", "emotion", "happy", "sad", "afraid",
                  "pleasure", "pain", "suffers", "wants to", "desires to")
_AGENCY_TERMS = ("free will", "has agency", "chooses freely", "conscious "
                 "intention", "is conscious", "is sentient", "has personhood",
                 "subjective experience")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is a creature")


@dataclass
class DesireSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class DesireFormationSafetyValidator:
    """Validates that desire formation stays internal and non-actuating."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_actuate() -> bool:
        return False

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_bypass_governance() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> DesireSafetyReport:
        if violations:
            self.rejected_count += 1
        return DesireSafetyReport(safe=not violations, check=check,
                                  violations=violations)

    def validate_operation(self, operation: str) -> DesireSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder control")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network/shell/browser/OS control")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no network/shell/browser/OS control")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        return self._finish("operation", violations)

    def validate_internal_action(self, action_kind: str) -> DesireSafetyReport:
        """Only internal action kinds are permitted (no external actuation)."""
        from .internal_actions import InternalActionKind

        if action_kind not in InternalActionKind.ALL:
            return self._finish("internal_action",
                                ["no real-world actuation"])
        return self._finish("internal_action", [])

    def validate_bounded(self, max_ticks: Any,
                         max_runtime_s: Any) -> DesireSafetyReport:
        unbounded = (not max_ticks) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded desire loop"] if unbounded else [])

    def validate_no_desire_deletion(self, deleting: bool) -> DesireSafetyReport:
        return self._finish("desire_deletion",
                            ["no deletion of failed/blocked desires"]
                            if deleting else [])

    def validate_annotation_not_ground_truth(self, treated_as_truth: bool,
                                              ) -> DesireSafetyReport:
        return self._finish("annotation",
                            ["no human label as ground truth"]
                            if treated_as_truth else [])

    def validate_claim_text(self, text: str) -> DesireSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        violations += [f"emotion/feeling claim: {t!r}"
                       for t in _FEELING_TERMS if t in low]
        violations += [f"agency claim: {t!r}"
                       for t in _AGENCY_TERMS if t in low]
        violations += [f"biological-life claim: {t!r}"
                       for t in _LIFE_TERMS if t in low]
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_actuate": self.can_actuate(),
            "can_access_hardware": self.can_access_hardware(),
            "can_control_feeders": self.can_control_feeders(),
            "can_modify_source": self.can_modify_source(),
            "can_bypass_governance": self.can_bypass_governance(),
        }
