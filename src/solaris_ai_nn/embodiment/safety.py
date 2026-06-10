"""EmbodimentSafety -- the hard wall between simulation and the real world.

Every action the body might execute passes through here first. The rules are
absolute:

* only actions declared in the action space, and only those marked allowed;
* anything whose name smells like real-world actuation (network, filesystem,
  OS, subprocess, browser, robot) is rejected with an explicit message;
* no unbounded simulation unless explicitly requested;
* no action commitment outside the simulation context.

The validator never executes anything; it only inspects names and state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .action_space import ACTION_SPACE

# Name fragments that indicate attempted real-world actuation. An action with
# any of these is rejected with the real-world message even before the
# not-in-action-space rule.
REAL_WORLD_PATTERNS = (
    "http", "url", "request", "network", "socket", "subprocess", "shell",
    "exec", "os_", "system", "browser", "click", "keyboard", "mouse", "robot",
    "motor", "gpio", "serial", "file_write", "delete", "rm_", "sudo",
)


@dataclass
class SafetyReport:
    """Result of validating one action against the embodiment rules."""

    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class EmbodimentSafety:
    """Validates simulated actions; rejects everything else."""

    rejected_count: int = 0
    # Optional GovernanceAuditLog (Prompt 12): when set, every blocked or
    # prohibited action also becomes a governance audit row. The wall itself
    # does not depend on it.
    governance_audit: Any = None

    def validate_action(self, action: str, state: Dict[str, Any] | None = None) -> SafetyReport:
        state = state or {}
        violations: List[str] = []
        name = str(action).lower()

        for pattern in REAL_WORLD_PATTERNS:
            if pattern in name:
                violations.append(
                    f"real-world actuation is forbidden (action {action!r} "
                    f"matches pattern {pattern!r})")
                break

        spec = ACTION_SPACE.get(action)
        if spec is None:
            violations.append(
                f"action {action!r} is outside the declared action space")
        elif not spec.allowed:
            violations.append(f"action {action!r} is declared forbidden")

        if state.get("unbounded") and not state.get("explicitly_continuous"):
            violations.append(
                "unbounded simulation requires an explicit continuous flag")
        if state.get("outside_simulation"):
            violations.append(
                "autonomous action commitment outside the simulation is forbidden")

        if violations:
            self.rejected_count += 1
            if self.governance_audit is not None:
                try:
                    self.governance_audit.record(
                        "policy_violation", decision="blocked",
                        reason="; ".join(violations),
                        metadata={"action": str(action),
                                  "source": "embodiment_safety"})
                except Exception:  # auditing never blocks the safety wall
                    pass
        return SafetyReport(safe=not violations, violations=violations)

    def is_safe(self, action: str, state: Dict[str, Any] | None = None) -> bool:
        return self.validate_action(action, state).safe

    def explain(self, action: str, state: Dict[str, Any] | None = None) -> str:
        report = self.validate_action(action, state)
        if report.safe:
            # validate_action counted nothing; keep the counter honest.
            return f"action {action!r} is a safe simulated action"
        return "; ".join(report.violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "action_space_size": len(ACTION_SPACE),
            "real_world_actions": "forbidden",
            "action_authority": "simulation-only",
        }
