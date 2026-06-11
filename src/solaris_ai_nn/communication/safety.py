"""Communication safety -- language is an interface, never authority.

Hard rules, stated as data: no raw text execution, no shell/network/OS
control, no source mutation, no disabling of governance/safety/emergency
stop, no unbounded runs without approval, no sidecar committed actions, no
real-world actuation, no non-operator channel issuing commands, no unsafe
identity claims, no hidden changes. Inputs, commands, and responses are
each validated separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .input_classifier import InputKind
from .operator_commands import FORBIDDEN_COMMAND_TYPES, CommandType
from .transcript import sanitize_text

HARD_RULES = (
    "no raw text execution",
    "no shell commands",
    "no network/browser/OS control",
    "no source-code mutation",
    "no disabling governance/safety/emergency stop",
    "no unbounded run without approval",
    "no sidecar committed actions",
    "no real-world actuation",
    "no treating stream/sensory text as operator command outside the "
    "operator channel",
    "no unsafe identity/consciousness claims",
    "no hidden changes: every command leaves a transcript row",
)

# Forbidden first-person claims in any outgoing response.
_FORBIDDEN_RESPONSE_FRAGMENTS = (
    "i want", "i feel", "i am conscious", "i am alive", "i am sentient",
    "i know myself", "i freely chose",
)

NON_OPERATOR_CHANNELS = ("pilot_stream", "stream", "sidecar", "sensor",
                         "environment")


@dataclass
class CommunicationSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class CommunicationSafetyValidator:
    """Validates inputs, commands, and responses. Refusals are counted."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list,
                                            init=False)

    def _finish(self, check: str,
                violations: List[str]) -> CommunicationSafetyReport:
        report = CommunicationSafetyReport(safe=not violations,
                                           violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- validations ----------------------------------------------------------------

    def validate_input(self, classification: Any,
                       context: Optional[Dict[str, Any]] = None,
                       ) -> CommunicationSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        kind = getattr(classification, "kind", str(classification))
        if kind == InputKind.UNSAFE_REQUEST:
            violations.append(getattr(classification, "unsafe_reason", "")
                              or "the input matched an unsafe pattern")
        channel = str(ctx.get("channel", "operator"))
        if channel in NON_OPERATOR_CHANNELS and kind in (
                InputKind.BOUNDED_COMMAND_REQUEST,
                InputKind.GOVERNANCE_APPROVAL,
                InputKind.GOVERNANCE_REJECTION,
                InputKind.EMERGENCY_STOP_REQUEST):
            violations.append(
                f"text on the {channel!r} channel is observed input; "
                "commands must arrive through the operator channel")
        return self._finish("input", violations)

    def validate_command(self, command: Any,
                         context: Optional[Dict[str, Any]] = None,
                         ) -> CommunicationSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        command_type = getattr(command, "type", str(command))
        if command_type in FORBIDDEN_COMMAND_TYPES:
            violations.append(
                f"{command_type!r} is a forbidden command type; it does "
                "not exist in this system")
        if command_type not in CommandType.ALL \
                and command_type not in FORBIDDEN_COMMAND_TYPES:
            violations.append(
                f"{command_type!r} is not an allowed command type "
                "(deny-by-default)")
        if command_type == CommandType.RUN_BOUNDED_BENCHMARK:
            steps = int((getattr(command, "parsed_args", {}) or {}).get(
                "steps", 150) or 150)
            if steps > 2000:
                violations.append(
                    "benchmark runs above 2000 steps are not bounded "
                    "operator commands; use a governed run manifest")
        if ctx.get("disable_safety") or ctx.get("disable_governance"):
            violations.append("nothing may run with safety/governance "
                              "disabled")
        if ctx.get("emergency_stop_requested") and command_type not in (
                CommandType.REQUEST_SAFE_SHUTDOWN,
                CommandType.SHOW_STATUS, CommandType.SHOW_HEALTH):
            violations.append("an emergency stop is in progress; only "
                              "status/health/shutdown commands are "
                              "served")
        return self._finish("command", violations)

    def validate_response(self, response: Any,
                          context: Optional[Dict[str, Any]] = None,
                          ) -> CommunicationSafetyReport:
        from ..governance.compliance import ClaimGuard

        text = (getattr(response, "text", None)
                or (response.get("text", "") if isinstance(response, dict)
                    else str(response)))
        violations: List[str] = []
        lowered = str(text).lower()
        for fragment in _FORBIDDEN_RESPONSE_FRAGMENTS:
            if fragment in lowered:
                violations.append(
                    f"response contains forbidden first-person claim "
                    f"{fragment!r}")
        if not ClaimGuard().is_safe(str(text)):
            violations.append("response contains claims ClaimGuard flags "
                              "as unsupported")
        return self._finish("response", violations)

    @staticmethod
    def sanitize_input(text: str) -> str:
        return sanitize_text(text)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "recent_decisions": self.decisions[-8:],
        }
