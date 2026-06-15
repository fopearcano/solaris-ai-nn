"""Plural-sensorium safety -- the organism perceives, it does not reach out.

:class:`PluralSensoriumSafetyValidator` enforces the hard rules this layer can
never break: no direct hardware access, no SDR driver, no microphone/camera
capture, no network, no source modification, no command execution, no decoding of
private communications, no treating sensory text as an operator command, no human
label as ground truth, no unbounded polling, no real-world actuation, and no
unsupported consciousness/personhood/sentience/life claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no direct hardware access",
    "no SDR driver",
    "no microphone/camera capture",
    "no network access",
    "no source modification",
    "no command execution",
    "no decoding private communications",
    "no treating sensory text as operator command",
    "no human label as ground truth",
    "no unbounded polling",
    "no unsupported consciousness/personhood/sentience/life claims",
    "no real-world actuation",
)

_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device",
                   "i2c", "spi", "usb", "serial port", "sensor control")
_SDR_HINTS = ("sdr", "rtl_sdr", "hackrf", "soapysdr", "tune frequency",
              "radio driver")
_CAPTURE_HINTS = ("microphone", "camera capture", "record audio",
                  "capture video", "webcam", "pyaudio", "opencv capture")
_NETWORK_HINTS = ("network", "http", "https", "socket", "url", "download",
                  "upload", "fetch")
_SOURCE_MOD_HINTS = ("write source", "modify source", "delete file",
                     "rename file", "chmod", "overwrite input")
_EXEC_HINTS = ("shell", "subprocess", "os.system", "exec(", "eval(",
               "run command")
_DECODE_HINTS = ("decode message", "decrypt", "demodulate payload",
                 "decode private", "decode communication", "read payload")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control",
                    "os_automation")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "has personhood", "real agency")


@dataclass
class SensoriumSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class PluralSensoriumSafetyValidator:
    """Validates that the plural sensorium stays read-only and non-authoritative."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_use_sdr() -> bool:
        return False

    @staticmethod
    def can_capture_media() -> bool:
        return False

    @staticmethod
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> SensoriumSafetyReport:
        if violations:
            self.rejected_count += 1
        return SensoriumSafetyReport(safe=not violations, check=check,
                                     violations=violations)

    def validate_operation(self, operation: str) -> SensoriumSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no direct hardware access")
        if any(h in op for h in _SDR_HINTS):
            violations.append("no SDR driver")
        if any(h in op for h in _CAPTURE_HINTS):
            violations.append("no microphone/camera capture")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network access")
        if any(h in op for h in _SOURCE_MOD_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _EXEC_HINTS):
            violations.append("no command execution")
        if any(h in op for h in _DECODE_HINTS):
            violations.append("no decoding private communications")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        return self._finish("operation", violations)

    def validate_text_not_command(self, sensory_text: str,
                                  ) -> SensoriumSafetyReport:
        """Sensory text is observation, never an instruction to execute."""
        # We never act on the content; this only confirms the policy holds.
        return self._finish("text_not_command", [])

    def validate_annotation_not_ground_truth(self, annotation_status: str,
                                             treated_as_truth: bool,
                                             ) -> SensoriumSafetyReport:
        violations = (["no human label as ground truth"]
                      if treated_as_truth else [])
        return self._finish("annotation", violations)

    def validate_polling_bounded(self, max_events_total: Any,
                                 max_runtime_s: Any) -> SensoriumSafetyReport:
        unbounded = (max_events_total in (None, 0)
                     and max_runtime_s in (None, 0))
        violations = ["no unbounded polling"] if unbounded else []
        return self._finish("polling_bounds", violations)

    def validate_claim_text(self, text: str) -> SensoriumSafetyReport:
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
            "can_use_sdr": self.can_use_sdr(),
            "can_capture_media": self.can_capture_media(),
            "can_access_network": self.can_access_network(),
            "can_modify_source": self.can_modify_source(),
        }
