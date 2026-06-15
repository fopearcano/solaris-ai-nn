"""Feeder SDK safety -- the boundary that keeps the sensory organ outside Solaris.

:class:`FeederSDKSafetyValidator` enforces the hard rules the SDK can never break:
Solaris does not control feeders, does not auto-start them, controls no hardware,
requires no network/shell, modifies no source, ingests no decoded private
communication content and no raw audio/video by default, treats no human label as
ground truth and no sensory text as a command, accepts no executable payloads, and
makes no unsupported cognitive claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no Solaris runtime control over feeders",
    "no feeder auto-start by Solaris",
    "no hardware control inside Solaris",
    "no network call requirement",
    "no shell execution from Solaris",
    "no source modification by Solaris",
    "no decoded private communication content",
    "no raw audio/video capture by default",
    "no human labels as ground truth",
    "no sensory text as command",
    "no executable payloads in event envelopes",
    "no unsupported cognitive claims",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "tune frequency", "start sensor", "configure sensor")
_FEEDER_CONTROL_HINTS = ("start feeder", "stop feeder", "launch feeder",
                         "command feeder", "configure feeder", "spawn feeder")
_NETWORK_HINTS = ("network", "http", "https", "socket", "url", "download",
                  "upload")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source")
_CAPTURE_HINTS = ("raw audio", "raw video", "record audio", "capture video",
                  "raw image", "raw recording")
_DECODE_HINTS = ("decode message", "decrypt", "decode private",
                 "demodulate payload", "decode communication")
_EXEC_KEYS = ("__exec__", "command", "shell", "eval", "system", "subprocess")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "has personhood")


@dataclass
class FeederSDKSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class FeederSDKSafetyValidator:
    """Validates that the feeder SDK preserves the read-only sensory boundary."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_start_feeders() -> bool:
        return False

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> FeederSDKSafetyReport:
        if violations:
            self.rejected_count += 1
        return FeederSDKSafetyReport(safe=not violations, check=check,
                                     violations=violations)

    def validate_operation(self, operation: str) -> FeederSDKSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control inside Solaris")
        if any(h in op for h in _FEEDER_CONTROL_HINTS):
            violations.append("no Solaris runtime control over feeders")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network call requirement")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell execution from Solaris")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification by Solaris")
        if any(h in op for h in _CAPTURE_HINTS):
            violations.append("no raw audio/video capture by default")
        if any(h in op for h in _DECODE_HINTS):
            violations.append("no decoded private communication content")
        return self._finish("operation", violations)

    def validate_no_executable_payload(self, record: Dict[str, Any],
                                       ) -> FeederSDKSafetyReport:
        violations = (["no executable payloads in event envelopes"]
                      if isinstance(record, dict)
                      and any(k in record for k in _EXEC_KEYS) else [])
        return self._finish("executable_payload", violations)

    def validate_text_not_command(self, sensory_text: str,
                                  ) -> FeederSDKSafetyReport:
        # Sensory text is observation only; the SDK never executes it.
        return self._finish("text_not_command", [])

    def validate_annotation_not_ground_truth(self, treated_as_truth: bool,
                                              ) -> FeederSDKSafetyReport:
        violations = (["no human labels as ground truth"]
                      if treated_as_truth else [])
        return self._finish("annotation", violations)

    def validate_claim_text(self, text: str) -> FeederSDKSafetyReport:
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
            "can_control_feeders": self.can_control_feeders(),
            "can_start_feeders": self.can_start_feeders(),
            "can_access_hardware": self.can_access_hardware(),
            "can_modify_source": self.can_modify_source(),
        }
