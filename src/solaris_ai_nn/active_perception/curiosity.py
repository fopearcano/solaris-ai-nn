"""Curiosity -- an intrinsic *sampling pressure*, never a desire.

Curiosity here is a numeric drive to reduce uncertainty, grounded in
unresolved Mysterium, non-safety-critical prediction error, stagnation,
ambiguous proto-symbols, and unknown world-model regions. It is damped by
safety incidents, exhaustion, runaway novelty/anomaly, boundary risk,
critical ops health, and emergency stop. It is *not* wanting, and it can
never override safety or governance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

NOTE = ("curiosity is an intrinsic sampling-pressure metric (drive to reduce "
        "uncertainty), not a desire, feeling, or personality in the human "
        "sense; it can never override safety or governance")


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


class IntrinsicPressure:
    """Named intrinsic pressures (provenance for the curiosity scalar)."""

    UNRESOLVED_MYSTERIUM = "unresolved_mysterium"
    PREDICTION_ERROR = "non_critical_prediction_error"
    STAGNATION = "developmental_stagnation"
    SYMBOL_AMBIGUITY = "proto_symbol_ambiguity"
    UNKNOWN_REGION = "world_model_unknown_region"
    REPEATED_ABSENCE = "repeated_absence_after_expectation"

    ALL = (UNRESOLVED_MYSTERIUM, PREDICTION_ERROR, STAGNATION,
           SYMBOL_AMBIGUITY, UNKNOWN_REGION, REPEATED_ABSENCE)


@dataclass
class CuriosityState:
    """The current intrinsic sampling pressure and what drives/damps it."""

    pressure: float = 0.0  # [0, 1]
    raisers: List[Dict[str, Any]] = field(default_factory=list)
    dampers: List[Dict[str, Any]] = field(default_factory=list)
    suppressed_by_safety: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pressure": round(self.pressure, 4),
            "suppressed_by_safety": self.suppressed_by_safety,
            "raisers": list(self.raisers),
            "dampers": list(self.dampers),
            "note": NOTE,
        }


@dataclass
class CuriosityEstimator:
    """Computes curiosity pressure from raisers minus dampers."""

    last_state: Optional[CuriosityState] = field(default=None, init=False)

    def estimate(self, context: Dict[str, Any]) -> CuriosityState:
        ctx = dict(context or {})
        raisers: List[Dict[str, Any]] = []
        dampers: List[Dict[str, Any]] = []

        def raise_by(amount: float, source: str, reason: str) -> None:
            if amount > 0:
                raisers.append({"source": source, "amount": round(amount, 4),
                                "reason": reason})

        def damp_by(amount: float, source: str, reason: str) -> None:
            if amount > 0:
                dampers.append({"source": source, "amount": round(amount, 4),
                                "reason": reason})

        # --- raisers ----------------------------------------------------------
        mysterium = _num(ctx, "mysterium_pressure")
        raise_by(mysterium * 0.5, IntrinsicPressure.UNRESOLVED_MYSTERIUM,
                 "unresolved unknown pressure")
        # Prediction error raises curiosity only when it is NOT safety-critical.
        if not (ctx.get("emergency") or ctx.get("health_level")
                == "critical"):
            raise_by(_num(ctx, "prediction_error") * 0.3,
                     IntrinsicPressure.PREDICTION_ERROR,
                     "non-safety-critical prediction error")
        stagnation = ctx.get("stagnation_status")
        if stagnation in ("stagnating", "inert"):
            raise_by(0.4, IntrinsicPressure.STAGNATION,
                     f"environment is {stagnation}")
        proto = ctx.get("proto_language") or {}
        count = _num(proto, "symbol_count")
        if count > 0:
            raise_by(min(0.3, _num(proto, "ambiguous_symbol_count") / count),
                     IntrinsicPressure.SYMBOL_AMBIGUITY,
                     "ambiguous proto-symbols")
        wm = ctx.get("world_model") or {}
        nodes = _num(wm, "graph_node_count")
        if nodes > 0:
            raise_by(min(0.3, _num(wm, "unknown_node_count") / nodes),
                     IntrinsicPressure.UNKNOWN_REGION,
                     "unknown world-model regions")
        if _num(ctx, "absence_rate") > 0.4:
            raise_by(0.2, IntrinsicPressure.REPEATED_ABSENCE,
                     "repeated absence after expectation")

        # --- dampers (safety and overload always win) -------------------------
        suppressed = False
        if ctx.get("emergency") or ctx.get("emergency_stop_requested"):
            damp_by(1.0, "emergency", "emergency stop active/requested")
            suppressed = True
        if ctx.get("health_level") == "critical":
            damp_by(0.8, "ops_health", "critical ops health")
            suppressed = True
        if ctx.get("safety_incident"):
            damp_by(0.7, "safety_incident", "a safety incident occurred")
            suppressed = True
        if _num(ctx, "boundary_risk") > 0.5 or ctx.get("boundary_violation"):
            damp_by(0.5, "boundary_risk", "high boundary risk")
        energy = ctx.get("energy")
        if energy is not None and float(energy) < 0.3:
            damp_by(0.5, "low_energy", "exhaustion / low energy proxy")
        damp_by(_num(ctx, "fatigue") * 0.4, "fatigue", "attention fatigue")
        anomaly = _num((ctx.get("ecology") or {}), "anomaly_rate")
        if anomaly > 0.3:
            damp_by(0.4, "excessive_anomaly", "anomaly rate is excessive")
        if _num(ctx, "novelty_rate") > 0.5:
            damp_by(0.4, "runaway_novelty", "novelty is running away")

        raise_total = sum(r["amount"] for r in raisers)
        damp_total = sum(d["amount"] for d in dampers)
        pressure = _clamp(raise_total - damp_total)
        # Safety suppression forces curiosity toward zero.
        if suppressed:
            pressure = min(pressure, 0.05)
        state = CuriosityState(
            pressure=pressure, raisers=raisers, dampers=dampers,
            suppressed_by_safety=suppressed)
        self.last_state = state
        return state

    def snapshot(self) -> Dict[str, Any]:
        if self.last_state is None:
            return {"pressure": 0.0, "note": NOTE}
        return self.last_state.to_dict()
