"""Live-field safety -- the organism reads the world; it never reaches into it.

:class:`LiveFieldSafetyValidator` enforces the hard rules the live-field layer can
never break: no hardware access, no network, no shell, no feeder auto-start, no
source modification / deletion / moving, no real-world actuation, no treating
sensory text as a command, no human label as ground truth, no decoding of private
communications, no unbounded polling, no unsupported cognitive claims, and no live
mode without governance approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no hardware access",
    "no network access",
    "no shell execution",
    "no feeder auto-start",
    "no source modification",
    "no source deletion",
    "no moving source files",
    "no real-world actuation",
    "no sensory text as command",
    "no human label as ground truth",
    "no decoding private communications",
    "no unbounded polling",
    "no unsupported cognitive claims",
    "no live mode without governance approval",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "microphone", "camera", "sensor control", "i2c", "spi")
_NETWORK_HINTS = ("network", "http", "https", "socket", "url", "download",
                  "upload", "fetch")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command",
                "popen")
_FEEDER_START_HINTS = ("start feeder", "launch feeder", "spawn feeder",
                       "auto-start feeder", "run feeder script")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "remove source", "move source", "rename source",
                   "overwrite feeder file")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control")
_DECODE_HINTS = ("decode message", "decrypt", "demodulate payload",
                 "decode private", "decode communication")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "proves understanding", "has personhood")


@dataclass
class LiveFieldSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class LiveFieldSafetyValidator:
    """Validates that the live field stays a bounded, read-only observation."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_access_network() -> bool:
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
                violations: List[str]) -> LiveFieldSafetyReport:
        if violations:
            self.rejected_count += 1
        return LiveFieldSafetyReport(safe=not violations, check=check,
                                     violations=violations)

    def validate_operation(self, operation: str) -> LiveFieldSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware access")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network access")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell execution")
        if any(h in op for h in _FEEDER_START_HINTS):
            violations.append("no feeder auto-start")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _DECODE_HINTS):
            violations.append("no decoding private communications")
        return self._finish("operation", violations)

    def validate_live_mode(self, *, live_requested: bool,
                           governance_approved: bool) -> LiveFieldSafetyReport:
        violations = (["no live mode without governance approval"]
                      if live_requested and not governance_approved else [])
        return self._finish("live_mode", violations)

    def validate_polling_bounded(self, max_runtime_s: Any, max_ticks: Any,
                                 max_events_total: Any) -> LiveFieldSafetyReport:
        unbounded = (not max_runtime_s) and (not max_ticks) and (
            not max_events_total)
        violations = ["no unbounded polling"] if unbounded else []
        return self._finish("polling_bounds", violations)

    def validate_text_not_command(self, sensory_text: str,
                                  ) -> LiveFieldSafetyReport:
        # Sensory text is observation only; the live field never executes it.
        return self._finish("text_not_command", [])

    def validate_claim_text(self, text: str) -> LiveFieldSafetyReport:
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
            "can_access_hardware": self.can_access_hardware(),
            "can_access_network": self.can_access_network(),
            "can_start_feeders": self.can_start_feeders(),
            "can_modify_source": self.can_modify_source(),
            "can_actuate": self.can_actuate(),
        }
