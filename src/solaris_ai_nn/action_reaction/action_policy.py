"""Action policy -- internal-only preferences learned from action consequences.

The :class:`ActionPolicyEngine` updates per-action-kind preferences (prefer / avoid
/ require more evidence / require simulation / require operator review / always
block forbidden external) based on learned effects, blocks, no-effect history,
overload reduction, and habit strength. Policy updates are internal only, cannot
authorize external action, and preserve the safety/governance veto.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class PolicyOutput:
    PREFER = "prefer_action_kind"
    AVOID = "avoid_action_kind"
    REQUIRE_MORE_EVIDENCE = "require_more_evidence"
    REQUIRE_SIMULATION_FIRST = "require_simulation_first"
    REQUIRE_CONSOLIDATION_FIRST = "require_consolidation_first"
    REQUIRE_OPERATOR_REVIEW = "require_operator_review"
    ALWAYS_BLOCK_FORBIDDEN = "always_block_forbidden_external"
    NO_CHANGE = "no_change"

    ALL = (PREFER, AVOID, REQUIRE_MORE_EVIDENCE, REQUIRE_SIMULATION_FIRST,
           REQUIRE_CONSOLIDATION_FIRST, REQUIRE_OPERATOR_REVIEW,
           ALWAYS_BLOCK_FORBIDDEN, NO_CHANGE)


@dataclass
class ActionPolicyUpdate:
    action_kind: str
    output: str
    update_id: str = field(default_factory=lambda: f"POL_{uuid.uuid4().hex[:8]}")
    reason: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"update_id": self.update_id, "action_kind": self.action_kind,
                "output": self.output, "reason": self.reason,
                "evidence_refs": list(self.evidence_refs),
                "note": "internal-only policy; cannot authorize external action; "
                        "safety/governance veto preserved"}


@dataclass
class ActionPolicy:
    """The current per-action-kind preferences (internal only)."""

    preferences: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"preferences": dict(self.preferences),
                "note": "internal preferences; forbidden external is always "
                        "blocked"}


@dataclass
class ActionPolicyEngine:
    """Updates internal action preferences from action consequences."""

    policy: ActionPolicy = field(default_factory=ActionPolicy)
    updates: List[ActionPolicyUpdate] = field(default_factory=list)

    def update_from_effects(self, effect_engine: Any, habit_engine: Any = None,
                            ) -> List[ActionPolicyUpdate]:
        new: List[ActionPolicyUpdate] = []
        for kind, model in getattr(effect_engine, "models", {}).items():
            if model.observations < 2:
                continue
            if model.success_rate >= 0.6:
                out = PolicyOutput.PREFER
                reason = f"repeated constructive reactions ({model.success_rate})"
            elif model.success_rate < 0.3:
                out = PolicyOutput.AVOID
                reason = f"repeated no-effect/disruptive ({model.success_rate})"
            else:
                out = PolicyOutput.REQUIRE_MORE_EVIDENCE
                reason = "mixed evidence"
            if self.policy.preferences.get(kind) != out:
                self.policy.preferences[kind] = out
                upd = ActionPolicyUpdate(action_kind=kind, output=out,
                                         reason=reason,
                                         evidence_refs=[f"effect:{kind}"])
                self.updates.append(upd)
                new.append(upd)
        # Forbidden external is always blocked, independent of evidence.
        if self.policy.preferences.get("forbidden_external") != \
                PolicyOutput.ALWAYS_BLOCK_FORBIDDEN:
            self.policy.preferences["forbidden_external"] = \
                PolicyOutput.ALWAYS_BLOCK_FORBIDDEN
            upd = ActionPolicyUpdate(
                action_kind="forbidden_external",
                output=PolicyOutput.ALWAYS_BLOCK_FORBIDDEN,
                reason="forbidden external actions are always blocked")
            self.updates.append(upd)
            new.append(upd)
        return new

    def to_dict(self) -> Dict[str, Any]:
        return {"policy": self.policy.to_dict(),
                "update_count": len(self.updates),
                "updates": [u.to_dict() for u in self.updates]}
