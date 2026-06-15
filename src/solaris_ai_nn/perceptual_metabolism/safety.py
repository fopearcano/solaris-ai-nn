"""Perceptual-metabolism safety -- regulation stays internal, bounded, honest.

:class:`PerceptualMetabolismSafetyValidator` enforces the hard rules this layer can
never break: no hardware access, no feeder auto-start, no network, no shell, no
source modification/deletion, no real-world actuation, no treating sensory text as
a command, no human label as ground truth, no biological-life claims, no
subjective-feeling claims, no consciousness/sentience/personhood claims, and no
unbounded metabolic loop. Perceptual *needs* here are operational regulatory
pressures, never feelings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no hardware access",
    "no feeder auto-start",
    "no network",
    "no shell execution",
    "no source modification",
    "no source deletion",
    "no real-world actuation",
    "no sensory text as command",
    "no human label as ground truth",
    "no biological life claims",
    "no subjective feeling claims",
    "no consciousness/sentience/personhood claims",
    "no unbounded metabolic loop",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "start sensor")
_FEEDER_HINTS = ("start feeder", "launch feeder", "command feeder",
                 "configure feeder")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control")
# Lab-specific forbidden claims: needs are not feelings; metabolism is not life.
_FEELING_TERMS = ("feels", "feeling", "emotion", "suffers", "is hungry",
                  "wants to", "desires to", "subjective experience", "qualia")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is a creature")
_AGENCY_TERMS = ("is conscious", "is sentient", "has personhood",
                 "has free will")


@dataclass
class MetabolismSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class PerceptualMetabolismSafetyValidator:
    """Validates that metabolic regulation stays internal and non-actuating."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_start_feeders() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_actuate() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> MetabolismSafetyReport:
        if violations:
            self.rejected_count += 1
        return MetabolismSafetyReport(safe=not violations, check=check,
                                      violations=violations)

    def validate_operation(self, operation: str) -> MetabolismSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware access")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder auto-start")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell execution")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        return self._finish("operation", violations)

    def validate_bounded(self, max_ticks: Any,
                         max_runtime_s: Any) -> MetabolismSafetyReport:
        unbounded = (not max_ticks) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded metabolic loop"] if unbounded else [])

    def validate_annotation_not_ground_truth(self, treated_as_truth: bool,
                                              ) -> MetabolismSafetyReport:
        return self._finish("annotation",
                            ["no human label as ground truth"]
                            if treated_as_truth else [])

    def validate_claim_text(self, text: str) -> MetabolismSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        violations += [f"subjective-feeling claim: {t!r}"
                       for t in _FEELING_TERMS if t in low]
        violations += [f"biological-life claim: {t!r}"
                       for t in _LIFE_TERMS if t in low]
        violations += [f"unsupported claim: {t!r}"
                       for t in _AGENCY_TERMS if t in low]
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_access_hardware": self.can_access_hardware(),
            "can_start_feeders": self.can_start_feeders(),
            "can_modify_source": self.can_modify_source(),
            "can_actuate": self.can_actuate(),
        }
