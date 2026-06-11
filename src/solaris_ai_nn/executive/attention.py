"""Attention -- a prioritization mechanism, not awareness.

The selector ranks possible focus targets from a context snapshot. The
ranking is fixed: emergency/safety always dominates, then operator review,
blocked repetition, energy, unknowns, plans, prediction failures, signal
bursts. Choosing a focus changes what the executive looks at first --
nothing more is claimed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# (target, priority, context predicate description). Highest priority wins.
FOCUS_RULES = (
    ("critical_safety_issue", 1.0,
     lambda ctx: ctx.get("health_level") == "critical"
     or ctx.get("emergency") or ctx.get("emergency_stop_requested")),
    ("operator_review_request", 0.9,
     lambda ctx: ctx.get("operator_review_pending")),
    ("blocked_repeated_action", 0.8,
     lambda ctx: int(ctx.get("repeated_blocked_actions", 0) or 0) >= 3),
    ("low_energy", 0.7,
     lambda ctx: ctx.get("exhausted")
     or float(ctx.get("energy_normalized", 1.0) or 1.0) < 0.25),
    ("recent_failed_prediction", 0.6,
     lambda ctx: int(ctx.get("prediction_miss_streak", 0) or 0) >= 3),
    ("high_mysterium_source", 0.55,
     lambda ctx: float(ctx.get("mysterium_pressure", 0.0) or 0.0) >= 0.6),
    ("world_model_unknown", 0.5,
     lambda ctx: int(ctx.get("unknown_node_count", 0) or 0) >= 5),
    ("sidecar_signal_burst", 0.45,
     lambda ctx: ctx.get("sidecar_signal_burst")),
    ("pilot_stream_anomaly", 0.45,
     lambda ctx: ctx.get("pilot_stream_anomaly")),
    ("current_plan", 0.4,
     lambda ctx: ctx.get("active_plan")),
    ("highest_urgency_need", 0.3,
     lambda ctx: ctx.get("dominant_need")),
)


@dataclass
class AttentionItem:
    """What the executive focuses on, and why."""

    target: str
    priority: float
    reason: str
    timestamp: float = field(default_factory=time.time)
    note: str = "a prioritization mechanism, not awareness"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AttentionSelector:
    """Ranks focus targets; safety always dominates."""

    history: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def rank_focus_items(self, context: Optional[Dict[str, Any]] = None,
                         ) -> List[AttentionItem]:
        ctx = context or {}
        items: List[AttentionItem] = []
        for target, priority, predicate in FOCUS_RULES:
            if predicate(ctx):
                reason = {
                    "critical_safety_issue": "health/emergency status is "
                                             "critical",
                    "low_energy": f"energy normalized "
                                  f"{ctx.get('energy_normalized')}",
                    "highest_urgency_need": f"dominant need "
                                            f"{ctx.get('dominant_need')!r}",
                    "high_mysterium_source": f"unknown pressure "
                                             f"{ctx.get('mysterium_pressure')}",
                }.get(target, f"context flagged {target}")
                items.append(AttentionItem(target=target,
                                           priority=priority,
                                           reason=reason))
        items.sort(key=lambda i: (-i.priority, i.target))
        return items

    def select_focus(self, context: Optional[Dict[str, Any]] = None,
                     ) -> AttentionItem:
        ranked = self.rank_focus_items(context)
        focus = (ranked[0] if ranked
                 else AttentionItem(target="ambient_monitoring",
                                    priority=0.1,
                                    reason="nothing demands focus"))
        self.history.append(focus.to_dict())
        self.history = self.history[-50:]
        return focus

    def snapshot(self) -> Dict[str, Any]:
        return {"recent_focus": self.history[-5:],
                "rules": [(t, p) for t, p, _ in FOCUS_RULES]}
