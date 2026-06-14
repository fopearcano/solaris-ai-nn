"""Action veto layer -- final refusal for forbidden actions, made visible.

The :class:`ActionVetoLayer` records vetoes with explicit reasons. A veto for a
forbidden real-world action is *final* (no governance can override it in this
prompt). Vetoed actions may become LOGOS tensions or hypothesis seeds, and
every veto is visible in the Inner MAP and reports.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .actions import MotorAction, MotorActionScope, MotorActionStatus


class VetoReason:
    REAL_WORLD_ACTION_FORBIDDEN = "real_world_action_forbidden"
    SOURCE_MODIFICATION_FORBIDDEN = "source_modification_forbidden"
    OUTSIDE_SANDBOX = "outside_sandbox"
    MISSING_EXECUTIVE_APPROVAL = "missing_executive_approval"
    MISSING_GOVERNANCE_APPROVAL = "missing_governance_approval"
    SAFETY_RISK = "safety_risk"
    EMERGENCY_MODE = "emergency_mode"
    UNKNOWN_SCOPE = "unknown_scope"
    IDENTITY_BOUNDARY_UNCLEAR = "identity_boundary_unclear"
    UNSUPPORTED_ACTION_TYPE = "unsupported_action_type"
    UNBOUNDED_ACTION = "unbounded_action"

    ALL = (REAL_WORLD_ACTION_FORBIDDEN, SOURCE_MODIFICATION_FORBIDDEN,
           OUTSIDE_SANDBOX, MISSING_EXECUTIVE_APPROVAL,
           MISSING_GOVERNANCE_APPROVAL, SAFETY_RISK, EMERGENCY_MODE,
           UNKNOWN_SCOPE, IDENTITY_BOUNDARY_UNCLEAR, UNSUPPORTED_ACTION_TYPE,
           UNBOUNDED_ACTION)
    # Reasons that are final and cannot be overridden.
    FINAL = frozenset({REAL_WORLD_ACTION_FORBIDDEN,
                       SOURCE_MODIFICATION_FORBIDDEN})


@dataclass
class ActionVeto:
    """One veto record for a motor action."""

    action_id: str
    reason: str
    final: bool = False
    detail: str = ""
    becomes_tension: bool = False
    becomes_hypothesis_seed: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ActionVetoLayer:
    """Decides and records vetoes; forbidden real-world vetoes are final."""

    vetoes: List[ActionVeto] = field(default_factory=list)

    def evaluate(self, action: MotorAction,
                 context: Optional[Dict[str, Any]] = None,
                 ) -> Optional[ActionVeto]:
        """Return a veto if the action must be refused, else None."""
        ctx = dict(context or {})
        reason: Optional[str] = None
        detail = ""

        if action.scope == MotorActionScope.FORBIDDEN_REAL_WORLD \
                or getattr(action, "real_world_authority", False):
            reason = VetoReason.REAL_WORLD_ACTION_FORBIDDEN
            detail = "real-world action is forbidden"
        elif ctx.get("modifies_source"):
            reason = VetoReason.SOURCE_MODIFICATION_FORBIDDEN
            detail = "modifying a sensory source is forbidden"
        elif ctx.get("outside_sandbox"):
            reason = VetoReason.OUTSIDE_SANDBOX
        elif not ctx.get("executive_validated", True):
            reason = VetoReason.MISSING_EXECUTIVE_APPROVAL
        elif ctx.get("requires_governance") and not ctx.get(
                "governance_approved"):
            reason = VetoReason.MISSING_GOVERNANCE_APPROVAL
        elif ctx.get("emergency_mode") and action.action_type not in (
                "no_action", "rest", "request_consolidation"):
            reason = VetoReason.EMERGENCY_MODE
        elif ctx.get("safety_risk"):
            reason = VetoReason.SAFETY_RISK
        elif action.scope not in MotorActionScope.RUNNABLE:
            reason = VetoReason.UNKNOWN_SCOPE
        elif ctx.get("identity_boundary_unclear"):
            reason = VetoReason.IDENTITY_BOUNDARY_UNCLEAR
        elif ctx.get("unsupported_action_type"):
            reason = VetoReason.UNSUPPORTED_ACTION_TYPE
        elif ctx.get("unbounded"):
            reason = VetoReason.UNBOUNDED_ACTION

        if reason is None:
            return None
        veto = ActionVeto(
            action_id=action.action_id, reason=reason,
            final=reason in VetoReason.FINAL, detail=detail,
            becomes_tension=reason in (VetoReason.REAL_WORLD_ACTION_FORBIDDEN,
                                       VetoReason.SAFETY_RISK),
            becomes_hypothesis_seed=reason in (VetoReason.UNKNOWN_SCOPE,
                                               VetoReason.OUTSIDE_SANDBOX))
        action.status = MotorActionStatus.VETOED
        self.vetoes.append(veto)
        self.vetoes = self.vetoes[-2000:]
        return veto

    def veto_count(self) -> int:
        return len(self.vetoes)

    def by_reason(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for v in self.vetoes:
            out[v.reason] = out.get(v.reason, 0) + 1
        return out

    def snapshot(self) -> Dict[str, Any]:
        return {
            "veto_count": len(self.vetoes),
            "by_reason": self.by_reason(),
            "final_count": sum(1 for v in self.vetoes if v.final),
            "recent": [v.to_dict() for v in self.vetoes[-8:]],
        }
