"""Attention control -- resource allocation, not awareness.

The :class:`ActiveAttentionController` chooses *where* the system spends its
bounded sampling attention inside the nursery / simulation / read-only
stream: a high-salience ecology event, an unknown world-model node, an
ambiguous proto-symbol, a recurring anomaly, a delayed-consequence group, a
boundary area, an absence window, a latent replay candidate, a homeostatic
pressure source, or an executive inhibition pattern. Emergency focus
overrides everything.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .salience import SalienceCategory, SalienceEstimator, SalienceMap


@dataclass
class AttentionFocus:
    """One focus target: what, why, and for how long."""

    target_ref: str
    source: str = ""
    category: str = SalienceCategory.CURIOSITY
    reason: str = ""
    held_until_step: int = 0
    emergency: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AttentionControlState:
    """The current focus and a bounded history of shifts."""

    current: Optional[AttentionFocus] = None
    shifts_total: int = field(default=0, init=False)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current": self.current.to_dict() if self.current else None,
            "shifts_total": self.shifts_total,
            "recent": self.history[-8:],
        }


@dataclass
class ActiveAttentionController:
    """Selects, holds, and releases attention focus deterministically."""

    salience: SalienceEstimator = field(default_factory=SalienceEstimator)
    state: AttentionControlState = field(default_factory=AttentionControlState)
    current_step: int = field(default=0, init=False)

    def select_focus(self, context: Dict[str, Any]) -> AttentionFocus:
        ctx = dict(context or {})
        self.current_step = int(ctx.get("step", self.current_step))
        smap: SalienceMap = (ctx.get("salience_map")
                             or self.salience.estimate(ctx))

        # Emergency focus overrides everything, including a held focus.
        if smap.has_safety_salience():
            top = next(s for s in smap.rank_targets(10)
                       if s.category == SalienceCategory.SAFETY)
            focus = AttentionFocus(
                target_ref=str(top.target_ref or top.source),
                source=top.source, category=top.category,
                reason=top.reason, emergency=True,
                held_until_step=self.current_step + 1)
            return self.shift_focus(focus, "emergency override")

        # Hold an existing non-expired focus.
        current = self.state.current
        if current and self.current_step < current.held_until_step \
                and not current.emergency:
            return current

        top = smap.top()
        if top is None:
            focus = AttentionFocus(
                target_ref="none", source="idle",
                category=SalienceCategory.CURIOSITY,
                reason="no salient target", held_until_step=self.current_step)
        else:
            focus = AttentionFocus(
                target_ref=str(top.target_ref or top.source),
                source=top.source, category=top.category, reason=top.reason,
                held_until_step=self.current_step + 1)
        return self.shift_focus(focus, top.reason if top else "idle")

    def shift_focus(self, target: AttentionFocus,
                    reason: str = "") -> AttentionFocus:
        if self.state.current is None \
                or self.state.current.target_ref != target.target_ref:
            self.state.shifts_total += 1
            self.state.history.append({
                "step": self.current_step,
                "from": (self.state.current.target_ref
                         if self.state.current else None),
                "to": target.target_ref, "reason": reason,
                "emergency": target.emergency})
            self.state.history = self.state.history[-100:]
        self.state.current = target
        return target

    def hold_focus(self, duration_steps: int) -> None:
        if self.state.current is not None:
            self.state.current.held_until_step = (
                self.current_step + max(1, int(duration_steps)))

    def release_focus(self, reason: str = "") -> None:
        if self.state.current is not None:
            self.state.history.append({
                "step": self.current_step,
                "from": self.state.current.target_ref, "to": None,
                "reason": reason or "released", "emergency": False})
            self.state.history = self.state.history[-100:]
        self.state.current = None

    def snapshot(self) -> Dict[str, Any]:
        return self.state.to_dict()
