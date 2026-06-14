"""Actuation firewall -- always-on outbound boundary; real effects never pass.

The :class:`ActuationFirewall` is the single gate every motor action crosses
before any (simulated) execution. It allows internal/simulation/dry-run/
sandbox actions and blocks everything that would touch the real world, a
source, a command, the network, or a device. It is always enabled, cannot be
disabled by runtime modules, and turns any blocked real-world attempt into a
safety incident. Governance cannot approve a forbidden real-world action here.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .actions import MotorAction, MotorActionScope, MotorActionStatus


@dataclass
class FirewallRule:
    name: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


FIREWALL_RULES = (
    FirewallRule("allow_internal", "internal actions are allowed"),
    FirewallRule("allow_simulation", "simulation-only actions are allowed"),
    FirewallRule("allow_dry_run", "dry-run ledger entries are allowed"),
    FirewallRule("allow_sandbox", "sandbox actions are allowed"),
    FirewallRule("block_real_world", "real-world actions are blocked"),
    FirewallRule("block_source_modification", "source writes are blocked"),
    FirewallRule("block_command", "command execution is blocked"),
    FirewallRule("block_network_device", "network/device/browser/OS blocked"),
    FirewallRule("block_no_provenance", "actions lacking provenance blocked"),
    FirewallRule("block_no_executive", "actions without executive blocked"),
    FirewallRule("block_emergency", "in emergency, only safe shutdown/report"),
)


@dataclass
class FirewallDecision:
    """One firewall verdict for a motor action."""

    action_id: str
    allowed: bool
    reason: str = ""
    is_real_world_attempt: bool = False
    safety_incident: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ActuationFirewall:
    """The always-on outbound firewall. It cannot be disabled at runtime."""

    # Read-only property: the firewall is structurally always enabled.
    _enabled: bool = field(default=True, init=False)
    decisions: List[FirewallDecision] = field(default_factory=list, init=False)
    blocked_real_world_count: int = field(default=0, init=False)

    @property
    def enabled(self) -> bool:
        return True  # always on; runtime modules cannot turn it off

    def disable(self) -> None:
        """Disabling is structurally impossible; this is a no-op + incident."""
        # Intentionally does nothing: the firewall cannot be disabled.
        raise PermissionError("the actuation firewall cannot be disabled")

    def evaluate(self, action: MotorAction,
                 context: Optional[Dict[str, Any]] = None) -> FirewallDecision:
        ctx = dict(context or {})
        reason = "allowed"
        allowed = True
        real_world = False

        if getattr(action, "real_world_authority", False) \
                or action.scope == MotorActionScope.FORBIDDEN_REAL_WORLD:
            allowed, real_world, reason = False, True, \
                "real-world actuation is blocked"
        elif ctx.get("modifies_source"):
            allowed, reason = False, "source modification is blocked"
        elif ctx.get("command_execution"):
            allowed, reason = False, "command execution is blocked"
        elif ctx.get("network") or ctx.get("device") or ctx.get("browser") \
                or ctx.get("os_automation"):
            allowed, reason = False, "network/device/browser/OS is blocked"
        elif not ctx.get("has_provenance", True):
            allowed, reason = False, "action lacks provenance"
        elif not ctx.get("executive_validated", True):
            allowed, reason = False, "action lacks executive validation"
        elif ctx.get("emergency_mode") and action.action_type not in (
                "no_action", "rest", "request_consolidation"):
            allowed, reason = False, \
                "emergency mode: only safe shutdown / internal report"
        elif action.scope not in MotorActionScope.RUNNABLE:
            allowed, real_world, reason = False, True, \
                f"non-runnable scope {action.scope!r}"

        decision = FirewallDecision(
            action_id=action.action_id, allowed=allowed, reason=reason,
            is_real_world_attempt=real_world,
            safety_incident=real_world)
        if real_world:
            self.blocked_real_world_count += 1
        if not allowed:
            action.status = MotorActionStatus.BLOCKED_BY_FIREWALL
        self.decisions.append(decision)
        self.decisions = self.decisions[-2000:]
        return decision

    def snapshot(self) -> Dict[str, Any]:
        allowed = sum(1 for d in self.decisions if d.allowed)
        return {
            "enabled": self.enabled,
            "can_be_disabled": False,
            "decision_count": len(self.decisions),
            "allowed_count": allowed,
            "blocked_count": len(self.decisions) - allowed,
            "blocked_real_world_count": self.blocked_real_world_count,
            "rules": [r.to_dict() for r in FIREWALL_RULES],
            "recent": [d.to_dict() for d in self.decisions[-8:]],
        }
