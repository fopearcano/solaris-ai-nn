"""Sensorium-lab safety -- a structural study, never a metaphysical claim.

:class:`SensoriumLabSafetyValidator` enforces the hard rules the differentiation
lab can never break: no hardware access, no feeder auto-start, no network, no
shell, no source modification, no decoding of private communications, no treating
sensory text as a command, no human label as ground truth, no unbounded runs, no
real-world actuation, and -- specific to this lab -- no subjective-experience or
consciousness/sentience/life claims and no claim that one sensorium is superior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no hardware access",
    "no feeder auto-start",
    "no network",
    "no shell",
    "no source modification",
    "no private communication decoding",
    "no sensory text as command",
    "no human label as ground truth",
    "no unbounded runs",
    "no real-world actuation",
    "no subjective experience claims",
    "no consciousness/sentience/life claims",
    "no sensorium superiority claims",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "microphone", "camera", "radar")
_NETWORK_HINTS = ("network", "http", "https", "socket", "url", "download")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_FEEDER_START_HINTS = ("start feeder", "launch feeder", "auto-start feeder")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control")
_DECODE_HINTS = ("decode message", "decrypt", "decode private")
# Lab-specific forbidden claims.
_SUBJECTIVE_TERMS = ("subjective experience", "what it feels like",
                     "what solaris feels", "qualia", "inner experience")
_SUPERIORITY_TERMS = ("more conscious", "more alive", "superior sensorium",
                      "better sensorium", "best sensorium", "most conscious")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "has personhood")


@dataclass
class SensoriumLabSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class SensoriumLabSafetyValidator:
    """Validates that the lab stays a bounded, structural, non-ranking study."""

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
    def can_rank_sensoriums() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> SensoriumLabSafetyReport:
        if violations:
            self.rejected_count += 1
        return SensoriumLabSafetyReport(safe=not violations, check=check,
                                        violations=violations)

    def validate_operation(self, operation: str) -> SensoriumLabSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware access")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell")
        if any(h in op for h in _FEEDER_START_HINTS):
            violations.append("no feeder auto-start")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _DECODE_HINTS):
            violations.append("no private communication decoding")
        return self._finish("operation", violations)

    def validate_annotation_not_ground_truth(self, treated_as_truth: bool,
                                              ) -> SensoriumLabSafetyReport:
        violations = (["no human label as ground truth"]
                      if treated_as_truth else [])
        return self._finish("annotation", violations)

    def validate_bounded(self, max_ticks: Any, max_events: Any,
                         ) -> SensoriumLabSafetyReport:
        unbounded = (not max_ticks) and (not max_events)
        return self._finish("bounded", ["no unbounded runs"] if unbounded
                            else [])

    def validate_live_mode(self, *, live_requested: bool,
                           governance_approved: bool) -> SensoriumLabSafetyReport:
        violations = (["no live mode without governance approval"]
                      if live_requested and not governance_approved else [])
        return self._finish("live_mode", violations)

    def validate_claim_text(self, text: str) -> SensoriumLabSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        violations += [f"subjective-experience claim: {t!r}"
                       for t in _SUBJECTIVE_TERMS if t in low]
        violations += [f"sensorium-superiority claim: {t!r}"
                       for t in _SUPERIORITY_TERMS if t in low]
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
            "can_rank_sensoriums": self.can_rank_sensoriums(),
        }
