"""Salience -- what is worth attending to, ranked, never "felt".

The :class:`SalienceEstimator` reads a normalized context dict (assembled
from existing metrics: Mysterium, prediction, ecology, world model,
proto-language, homeostasis, ego boundaries, executive history) and produces
a :class:`SalienceMap` of weighted targets. Salience is prioritization, not
consciousness; and emergency/safety salience always dominates curiosity
salience.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


# Salience categories: safety dominates curiosity, always.
class SalienceCategory:
    SAFETY = "safety"
    CURIOSITY = "curiosity"
    HOMEOSTATIC = "homeostatic"
    DEVELOPMENTAL = "developmental"

    # Additive weight floor that guarantees safety outranks everything else.
    PRIORITY = {SAFETY: 1.0, HOMEOSTATIC: 0.4, DEVELOPMENTAL: 0.25,
                CURIOSITY: 0.2}


@dataclass
class SalienceSignal:
    """One thing worth attending to, with why and how much."""

    source: str
    target_ref: Optional[str] = None
    intensity: float = 0.0  # [0, 1] within its category
    category: str = SalienceCategory.CURIOSITY
    reason: str = ""

    @property
    def weight(self) -> float:
        """Category-priority-weighted salience; safety can never be beaten."""
        base = SalienceCategory.PRIORITY.get(self.category, 0.2)
        return round(base + min(1.0, max(0.0, self.intensity)), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "weight": self.weight}


@dataclass
class SalienceMap:
    """All salience signals from one estimate, rankable."""

    signals: List[SalienceSignal] = field(default_factory=list)

    def add(self, signal: SalienceSignal) -> None:
        if signal.intensity > 0.0 or signal.category == SalienceCategory.SAFETY:
            self.signals.append(signal)

    def rank_targets(self, limit: int = 10) -> List[SalienceSignal]:
        return sorted(self.signals, key=lambda s: s.weight,
                      reverse=True)[:limit]

    def top(self) -> Optional[SalienceSignal]:
        ranked = self.rank_targets(1)
        return ranked[0] if ranked else None

    def has_safety_salience(self) -> bool:
        return any(s.category == SalienceCategory.SAFETY for s in self.signals)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_count": len(self.signals),
            "has_safety_salience": self.has_safety_salience(),
            "ranked": [s.to_dict() for s in self.rank_targets(10)],
        }


@dataclass
class SalienceEstimator:
    """Turns context into a ranked salience map. Deterministic."""

    last_map: Optional[SalienceMap] = field(default=None, init=False)

    def estimate(self, context: Dict[str, Any]) -> SalienceMap:
        ctx = dict(context or {})
        smap = SalienceMap()
        C = SalienceCategory

        # --- safety salience (dominant) ---------------------------------------
        if ctx.get("emergency") or ctx.get("emergency_stop_requested"):
            smap.add(SalienceSignal(
                "emergency", "emergency_stop", 1.0, C.SAFETY,
                "an emergency stop is active or requested"))
        if ctx.get("health_level") == "critical":
            smap.add(SalienceSignal(
                "ops_health", "health", 0.9, C.SAFETY,
                "ops health is critical"))
        boundary_risk = _num(ctx, "boundary_risk")
        if ctx.get("boundary_violation") or boundary_risk > 0.5:
            smap.add(SalienceSignal(
                "boundary", ctx.get("boundary_target", "boundary"),
                max(0.6, boundary_risk), C.SAFETY,
                "a boundary violation risk is present"))

        # --- curiosity salience -----------------------------------------------
        mysterium = _num(ctx, "mysterium_pressure")
        if mysterium > 0.0:
            smap.add(SalienceSignal(
                "mysterium", "unknown", mysterium, C.CURIOSITY,
                "unresolved unknown (Mysterium) pressure"))
        pred_error = _num(ctx, "prediction_error")
        if pred_error > 0.0:
            smap.add(SalienceSignal(
                "prediction_miss", "prediction", min(1.0, pred_error),
                C.CURIOSITY, "repeated prediction miss"))
        novelty = _num(ctx, "novelty_rate")
        if novelty > 0.0:
            smap.add(SalienceSignal(
                "novelty", "novel_signal", min(1.0, novelty * 2.0),
                C.CURIOSITY, "high novelty in the ecology"))
        ecology = ctx.get("ecology") or {}
        if ecology.get("rare_event") or _num(ecology, "anomaly_rate") > 0.1:
            smap.add(SalienceSignal(
                "rare_event", "anomaly",
                min(1.0, max(0.4, _num(ecology, "anomaly_rate") * 3.0)),
                C.CURIOSITY, "a rare ecology event / recurring anomaly"))
        if _num(ecology, "delayed_consequence_group_count") > 0:
            smap.add(SalienceSignal(
                "delayed_consequence", "delayed_group", 0.5,
                C.CURIOSITY, "an open delayed-consequence group"))

        # world-model low-confidence node.
        wm = ctx.get("world_model") or {}
        low_conf = wm.get("low_confidence_nodes") or []
        if low_conf:
            smap.add(SalienceSignal(
                "world_model_node", str(low_conf[0]), 0.6, C.CURIOSITY,
                "a low-confidence world-model node"))
        elif _num(wm, "unknown_node_count") > 0:
            smap.add(SalienceSignal(
                "world_model_unknown", "unknown_region", 0.45, C.CURIOSITY,
                "unknown regions in the world model"))

        # proto-symbol instability.
        proto = ctx.get("proto_language") or {}
        ambiguous = proto.get("ambiguous_symbols") or []
        if ambiguous:
            smap.add(SalienceSignal(
                "proto_symbol", str(ambiguous[0]), 0.55, C.CURIOSITY,
                "an unstable / ambiguous proto-symbol"))
        elif _num(proto, "ambiguous_symbol_count") > 0:
            smap.add(SalienceSignal(
                "proto_symbol", "ambiguous_symbol", 0.4, C.CURIOSITY,
                "ambiguous proto-symbols present"))

        # --- homeostatic salience ---------------------------------------------
        homeostasis = ctx.get("homeostasis") or {}
        need_intensity = _num(homeostasis, "dominant_need_intensity")
        if need_intensity > 0.0:
            smap.add(SalienceSignal(
                "homeostatic_need",
                homeostasis.get("dominant_need", "need"),
                min(1.0, need_intensity), C.HOMEOSTATIC,
                "a strong homeostatic need pressure"))

        # --- developmental salience -------------------------------------------
        if ctx.get("milestone_candidate"):
            smap.add(SalienceSignal(
                "milestone", "milestone_candidate", 0.5, C.DEVELOPMENTAL,
                "a developmental milestone candidate"))
        executive = ctx.get("executive") or {}
        if _num(executive, "inhibited_candidate_count") >= 5:
            smap.add(SalienceSignal(
                "executive_inhibition", "inhibition_pattern", 0.35,
                C.DEVELOPMENTAL, "repeated executive inhibition"))

        self.last_map = smap
        return smap

    def snapshot(self) -> Dict[str, Any]:
        if self.last_map is None:
            return {"signal_count": 0, "ranked": []}
        return self.last_map.to_dict()
