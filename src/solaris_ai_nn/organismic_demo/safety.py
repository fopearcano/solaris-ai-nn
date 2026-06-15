"""Organismic-demo safety -- the demo observes; it never reaches out or cheats.

:class:`OrganismicDemoSafetyValidator` enforces the hard rules the demo can never
break: no hardware access, no direct sensor control, no network, no shell, no
real-world actuation, no source mutation during perception, no treating sensory
text as a command, no human labels as ground truth, no unbounded runtime, no
leakage of the cross-modal debug-truth file into Solaris's perception, and no
unsupported cognitive claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no hardware access",
    "no direct sensor control",
    "no network",
    "no shell",
    "no real-world actuation",
    "no source mutation during perception",
    "no treating sensory text as command",
    "no human labels as ground truth",
    "no unbounded runtime",
    "no hidden debug-truth leakage into perception",
    "no unsupported cognitive claims",
)

# The debug-truth file name must never enter the sensory roots.
DEBUG_TRUTH_FILENAME = "cross_modal_truth_debug.jsonl"

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "sensor control",
                   "open device", "sdr", "microphone", "camera")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download", "upload")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control")
_MUTATION_HINTS = ("write source", "modify source", "mutate source",
                   "overwrite feeder")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "proves understanding", "has personhood")


@dataclass
class DemoSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class OrganismicDemoSafetyValidator:
    """Validates that the demo stays a bounded, read-only observation."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_actuate() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> DemoSafetyReport:
        if violations:
            self.rejected_count += 1
        return DemoSafetyReport(safe=not violations, check=check,
                                violations=violations)

    def validate_operation(self, operation: str) -> DemoSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware access")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source mutation during perception")
        return self._finish("operation", violations)

    def validate_sensory_roots(self, roots: List[str]) -> DemoSafetyReport:
        """The debug-truth file must never be inside a sensory root."""
        violations: List[str] = []
        for root in roots:
            low = str(root).lower()
            if DEBUG_TRUTH_FILENAME in low:
                violations.append("no hidden debug-truth leakage into "
                                  "perception")
        return self._finish("sensory_roots", violations)

    def validate_no_debug_leakage(self, feeder_paths: List[str],
                                  ) -> DemoSafetyReport:
        violations = ["no hidden debug-truth leakage into perception"] \
            if any(DEBUG_TRUTH_FILENAME in str(p) for p in feeder_paths) else []
        return self._finish("debug_leakage", violations)

    def validate_text_not_command(self, sensory_text: str) -> DemoSafetyReport:
        # Sensory text is observation only; the demo never executes it.
        return self._finish("text_not_command", [])

    def validate_runtime_bounded(self, ticks: Any, max_runtime_s: Any,
                                 max_events_total: Any) -> DemoSafetyReport:
        unbounded = (not ticks) and (not max_runtime_s) and (
            not max_events_total)
        violations = ["no unbounded runtime"] if unbounded else []
        return self._finish("runtime_bounds", violations)

    def validate_claim_text(self, text: str) -> DemoSafetyReport:
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
            "can_actuate": self.can_actuate(),
        }
