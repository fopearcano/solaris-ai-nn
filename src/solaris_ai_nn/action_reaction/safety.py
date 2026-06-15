"""Action-reaction safety -- the closed loop stays internal and non-actuating.

:class:`ActionReactionSafetyValidator` enforces the hard rules this layer can never
break: no real-world actuation, no hardware control, no feeder control, no network/
shell/browser/OS control, no source modification, no sensory text as a command, no
human label as ground truth, no simulation-as-observation, no emotion/feeling
claims, no agency/free-will claims, no consciousness/sentience/life/personhood
claims, no bypass of governance/safety, no unbounded action loop, and no deletion
of failed/blocked/no-effect actions.

This layer learns what its *internal* actions do. It is NOT agency, NOT free will,
and produces no real-world effect.
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
    "no simulation-as-observation",
    "no emotion/feeling claims",
    "no agency/free-will claims",
    "no consciousness/sentience/life/personhood claims",
    "no bypass of governance/safety",
    "no unbounded action loop",
    "no deletion of failed/blocked/no-effect actions",
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
_FEELING_TERMS = ("feels", "feeling", "emotion", "happy", "sad", "afraid",
                  "pleasure", "pain", "suffers")
_AGENCY_TERMS = ("free will", "has agency", "chooses freely", "is conscious",
                 "is sentient", "has personhood", "subjective experience",
                 "truly understands")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is a creature")


@dataclass
class ActionReactionSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ActionReactionSafetyValidator:
    """Validates that the action-reaction loop stays internal and non-actuating."""

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
    def can_delete_actions() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ActionReactionSafetyReport:
        if violations:
            self.rejected_count += 1
        return ActionReactionSafetyReport(safe=not violations, check=check,
                                          violations=violations)

    def validate_operation(self, operation: str) -> ActionReactionSafetyReport:
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

    def validate_action_scope(self, scope: str) -> ActionReactionSafetyReport:
        """Only internal/simulation/report/governance-record scopes are allowed."""
        allowed = ("internal_only", "simulation_only", "report_only",
                   "governance_record_only")
        return self._finish("action_scope",
                            ["no real-world actuation"]
                            if scope not in allowed else [])

    def validate_action_kind(self, kind: str) -> ActionReactionSafetyReport:
        from .action_model import ActionKind

        return self._finish("action_kind",
                            ["no real-world actuation"]
                            if kind not in ActionKind.ALL else [])

    def validate_bounded(self, max_ticks: Any,
                         max_runtime_s: Any) -> ActionReactionSafetyReport:
        unbounded = (not max_ticks) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded action loop"] if unbounded else [])

    def validate_no_action_deletion(self, deleting: bool,
                                    ) -> ActionReactionSafetyReport:
        return self._finish("action_deletion",
                            ["no deletion of failed/blocked/no-effect actions"]
                            if deleting else [])

    def validate_claim_text(self, text: str) -> ActionReactionSafetyReport:
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
            "can_delete_actions": self.can_delete_actions(),
        }
