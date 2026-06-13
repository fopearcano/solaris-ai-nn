"""Stagnation -- is development stalling, racing, or healthily quiet?

Stagnation is not always bad: a stable phase with little change can be fine.
The :class:`StagnationDetector` reads recent structural-change, symbol,
world-model, prediction, and Mysterium signals and reports a *cautious*
status (stable / stagnating / inert / overactive / unknown), then recommends
an intrinsic sampling pressure adjustment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


class StagnationStatus:
    STABLE = "stable"
    STAGNATING = "stagnating"
    INERT = "inert"
    OVERACTIVE = "overactive"
    UNKNOWN = "unknown"

    ALL = (STABLE, STAGNATING, INERT, OVERACTIVE, UNKNOWN)


@dataclass
class StagnationState:
    """The cautious stagnation verdict, with the evidence behind it."""

    status: str = StagnationStatus.UNKNOWN
    indicators: List[str] = field(default_factory=list)
    structural_change: float = 0.0
    mysterium: float = 0.0
    recommended_sampling_pressure: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "indicators": list(self.indicators),
            "structural_change": round(self.structural_change, 4),
            "mysterium": round(self.mysterium, 4),
            "recommended_sampling_pressure": round(
                self.recommended_sampling_pressure, 4),
        }


@dataclass
class StagnationDetector:
    """Detects flat / racing development from recent windows."""

    flat_change_threshold: float = 0.02
    overactive_change_threshold: float = 0.6
    _change_history: List[float] = field(default_factory=list, init=False)
    last_state: Optional[StagnationState] = field(default=None, init=False)

    def detect(self, context: Dict[str, Any]) -> StagnationState:
        ctx = dict(context or {})
        developmental = ctx.get("developmental") or {}
        change = _num(developmental, "structural_change_score",
                      _num(ctx, "structural_change_score"))
        self._change_history.append(change)
        self._change_history = self._change_history[-20:]
        mysterium = _num(ctx, "mysterium_pressure")
        indicators: List[str] = []

        wm = ctx.get("world_model") or {}
        proto = ctx.get("proto_language") or {}
        executive = ctx.get("executive") or {}

        flat_growth = change <= self.flat_change_threshold
        no_new_symbols = _num(proto, "stable_symbol_count") == 0 \
            and _num(proto, "symbol_count") > 0
        wm_flat = ctx.get("world_model_growth_flat", False)
        pred_flat = ctx.get("prediction_accuracy_flat", False)
        no_action_loop = _num(executive, "no_safe_action_count") >= 5
        repeat = _num(ctx, "repeated_action_count")
        over_consolidation = ctx.get("excessive_consolidation", False)

        if flat_growth:
            indicators.append("structural growth is flat")
        if no_new_symbols:
            indicators.append("no stable symbol emergence")
        if wm_flat:
            indicators.append("world-model growth flat")
        if pred_flat:
            indicators.append("prediction accuracy flat")
        if no_action_loop:
            indicators.append("executive no-action loop")
        if repeat >= 8:
            indicators.append("repeated same action/suggestion")
        if over_consolidation:
            indicators.append("excessive consolidation without new structure")

        # --- cautious classification -----------------------------------------
        evidence = any(k in ctx or k in developmental for k in (
            "structural_change_score", "developmental", "mysterium_pressure"))
        if not evidence:
            status = StagnationStatus.UNKNOWN
        elif change >= self.overactive_change_threshold \
                or _num(ctx, "novelty_rate") > 0.5:
            status = StagnationStatus.OVERACTIVE
            indicators.append("change/novelty is racing")
        elif flat_growth and mysterium < 0.2 and len(indicators) <= 1:
            # Flat and calm with no unresolved unknown: a stable phase is OK.
            status = StagnationStatus.STABLE
        elif flat_growth and mysterium >= 0.5:
            # Flat growth while unknown pressure stays high: genuinely stuck.
            status = StagnationStatus.STAGNATING
        elif flat_growth and len(indicators) >= 3:
            status = StagnationStatus.INERT
        elif flat_growth:
            status = StagnationStatus.STAGNATING
        else:
            status = StagnationStatus.STABLE

        recommended = self.recommend_sampling_pressure(status)
        state = StagnationState(
            status=status, indicators=indicators,
            structural_change=change, mysterium=mysterium,
            recommended_sampling_pressure=recommended)
        self.last_state = state
        return state

    def recommend_sampling_pressure(self, state: Any) -> float:
        """How much extra intrinsic sampling pressure to apply."""
        status = state if isinstance(state, str) else getattr(
            state, "status", StagnationStatus.UNKNOWN)
        return {
            StagnationStatus.STABLE: 0.1,
            StagnationStatus.STAGNATING: 0.5,
            StagnationStatus.INERT: 0.7,
            StagnationStatus.OVERACTIVE: 0.0,  # already too much; do not add
            StagnationStatus.UNKNOWN: 0.2,
        }.get(status, 0.2)

    def snapshot(self) -> Dict[str, Any]:
        if self.last_state is None:
            return {"status": StagnationStatus.UNKNOWN, "indicators": []}
        return self.last_state.to_dict()
