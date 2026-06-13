"""Complexity regulation -- a bounded productive middle, not a life score.

The :class:`ComplexityRegulator` combines pressure sources (symbol count and
ambiguity, world-model edge density, hypothesis count, unresolved tension
count, Mysterium, novelty, memory, drift, executive conflict, homeostatic
instability, auto-regeneration degradation) into a :class:`ComplexityState`
with a band -- inert / simple_stable / productive / complex_unstable /
overloaded / unknown -- and a recommendation. Too little complexity can mean
an inert/dead system; too much means overload; productive complexity is the
bounded middle. This is **not** a consciousness or life score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


class ComplexityBand:
    INERT = "inert"
    SIMPLE_STABLE = "simple_stable"
    PRODUCTIVE = "productive"
    COMPLEX_UNSTABLE = "complex_unstable"
    OVERLOADED = "overloaded"
    UNKNOWN = "unknown"

    ALL = (INERT, SIMPLE_STABLE, PRODUCTIVE, COMPLEX_UNSTABLE, OVERLOADED,
           UNKNOWN)


class ComplexityRecommendation:
    PRESERVE = "preserve_current_mode"
    INCREASE_EXPLORATION = "increase_exploration"
    INCREASE_CONSOLIDATION = "increase_consolidation"
    REDUCE_SAMPLING = "reduce_sampling"
    REQUEST_PRUNING = "request_pruning"
    REQUEST_LATENT_REPLAY = "request_latent_replay"
    REQUEST_AUTO_REGENERATION = "request_auto_regeneration"
    REQUEST_SAFE_SHUTDOWN = "request_safe_shutdown"

    ALL = (PRESERVE, INCREASE_EXPLORATION, INCREASE_CONSOLIDATION,
           REDUCE_SAMPLING, REQUEST_PRUNING, REQUEST_LATENT_REPLAY,
           REQUEST_AUTO_REGENERATION, REQUEST_SAFE_SHUTDOWN)


@dataclass
class ComplexityPressure:
    """The decomposed pressure inputs for one complexity estimate."""

    sources: Dict[str, float] = field(default_factory=dict)

    @property
    def score(self) -> float:
        if not self.sources:
            return 0.0
        return round(min(1.0, sum(self.sources.values())
                         / max(1, len(self.sources))), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {"sources": {k: round(v, 4) for k, v in self.sources.items()},
                "score": self.score}


@dataclass
class ComplexityState:
    """The complexity band and the recommendation that follows from it."""

    band: str = ComplexityBand.UNKNOWN
    pressure: ComplexityPressure = field(default_factory=ComplexityPressure)
    recommendation: str = ComplexityRecommendation.PRESERVE
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "band": self.band,
            "pressure": self.pressure.to_dict(),
            "recommendation": self.recommendation,
            "reasons": list(self.reasons),
        }


@dataclass
class ComplexityRegulator:
    """Estimates the complexity band and recommends a bounded response."""

    history: List[str] = field(default_factory=list)
    last_state: Optional[ComplexityState] = field(default=None, init=False)
    overload_warnings: int = field(default=0, init=False)
    inert_warnings: int = field(default=0, init=False)

    def estimate(self, context: Dict[str, Any]) -> ComplexityState:
        ctx = dict(context or {})
        proto = ctx.get("proto_language") or {}
        wm = ctx.get("world_model") or {}
        hyp = ctx.get("hypothesis") or {}
        ap = ctx.get("active_perception") or {}
        drift = ctx.get("drift") or {}
        memory = ctx.get("memory") or {}
        executive = ctx.get("executive") or {}
        homeostasis = ctx.get("homeostasis") or {}
        ar = ctx.get("autoregeneration") or {}

        sym_count = _num(proto, "symbol_count")
        nodes = _num(wm, "graph_node_count")
        edges = _num(wm, "graph_edge_count")
        pressure = ComplexityPressure(sources={
            "symbol_count": _clamp(sym_count / 500.0),
            "symbol_ambiguity": _clamp(
                _num(proto, "ambiguous_symbol_count")
                / max(1.0, sym_count)),
            "edge_density": _clamp((edges / nodes / 5.0) if nodes else 0.0),
            "hypothesis_count": _clamp(_num(hyp, "hypothesis_count") / 200.0),
            "unresolved_tensions": _clamp(
                _num(ctx, "unresolved_tension_count") / 10.0),
            "mysterium": _num(ctx, "mysterium_pressure"),
            "novelty": _num(ap, "curiosity_pressure",
                            _num(ctx, "novelty_rate")),
            "memory": (1.0 if memory.get("over_budget") else 0.0),
            "drift_velocity": _clamp(_num(drift, "drift_velocity") / 3.0),
            "executive_conflict": _clamp(
                _num(executive, "no_safe_action_count") / 10.0),
            "homeostatic_instability": _clamp(
                _num(homeostasis, "conflict_count") / 5.0),
            "autoregeneration_degradation":
                {"info": 0.0, "watch": 0.3, "warning": 0.6,
                 "critical": 0.9}.get(
                     str(ar.get("latest_degradation_severity", "info")),
                     0.0),
        })
        band, reasons = self._band(pressure, ctx)
        recommendation = self._recommend(band, ctx)
        state = ComplexityState(band=band, pressure=pressure,
                                recommendation=recommendation, reasons=reasons)
        if band == ComplexityBand.OVERLOADED:
            self.overload_warnings += 1
        if band == ComplexityBand.INERT:
            self.inert_warnings += 1
        self.history.append(band)
        self.history = self.history[-200:]
        self.last_state = state
        return state

    def _band(self, pressure: ComplexityPressure,
              ctx: Dict[str, Any]) -> "tuple[str, List[str]]":
        score = pressure.score
        reasons: List[str] = [f"pressure score {score}"]
        if not any(ctx.get(k) for k in ("proto_language", "world_model",
                                        "hypothesis", "mysterium_pressure",
                                        "active_perception")):
            return (ComplexityBand.UNKNOWN, ["insufficient evidence"])
        critical = (ctx.get("emergency")
                    or ctx.get("health_level") == "critical"
                    or str((ctx.get("autoregeneration") or {}).get(
                        "latest_degradation_severity")) == "critical")
        # The score is a mean over many sources, so it stays modest even
        # under real load; the band thresholds are calibrated accordingly.
        if critical or score >= 0.45:
            return (ComplexityBand.OVERLOADED,
                    reasons + ["critical/very high pressure"])
        if score >= 0.25:
            return (ComplexityBand.COMPLEX_UNSTABLE,
                    reasons + ["high pressure, not yet overloaded"])
        if score >= 0.05:
            return (ComplexityBand.PRODUCTIVE,
                    reasons + ["bounded productive middle"])
        if ctx.get("stagnation_status") in ("stagnating", "inert") \
                and score < 0.03:
            return (ComplexityBand.INERT,
                    reasons + ["near-zero change/pressure"])
        return (ComplexityBand.SIMPLE_STABLE, reasons + ["low, stable"])

    def _recommend(self, band: str, ctx: Dict[str, Any]) -> str:
        R = ComplexityRecommendation
        if ctx.get("emergency") or ctx.get("health_level") == "critical":
            return R.REQUEST_SAFE_SHUTDOWN
        return {
            ComplexityBand.OVERLOADED: R.REQUEST_AUTO_REGENERATION,
            ComplexityBand.COMPLEX_UNSTABLE: R.INCREASE_CONSOLIDATION,
            ComplexityBand.PRODUCTIVE: R.PRESERVE,
            ComplexityBand.SIMPLE_STABLE: R.PRESERVE,
            ComplexityBand.INERT: R.INCREASE_EXPLORATION,
            ComplexityBand.UNKNOWN: R.PRESERVE,
        }.get(band, R.PRESERVE)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "band": self.last_state.band if self.last_state
            else ComplexityBand.UNKNOWN,
            "overload_warnings": self.overload_warnings,
            "inert_warnings": self.inert_warnings,
            "last_state": (self.last_state.to_dict()
                           if self.last_state else None),
            "band_distribution": {b: self.history.count(b)
                                  for b in set(self.history)},
        }
