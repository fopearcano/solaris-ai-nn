"""Uncertainty -- where the system's model is weakest, grounded in metrics.

The :class:`UncertaintyEstimator` aggregates uncertainty from existing
signals (world-model prediction confidence, proto-symbol ambiguity,
anticipation misses, weak causal candidates, Mysterium, counterfactual
divergence, repeated anomalies, conflicting executive outcomes, ego
attribution uncertainty, memory compression loss). When evidence is
insufficient it reports *unknown* rather than inventing a target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


class UncertaintySource:
    WORLD_MODEL_CONFIDENCE = "world_model_confidence"
    PROTO_SYMBOL_AMBIGUITY = "proto_symbol_ambiguity"
    ANTICIPATION_MISS = "anticipation_miss"
    WEAK_CAUSAL_CANDIDATE = "weak_causal_candidate"
    MYSTERIUM = "mysterium"
    COUNTERFACTUAL_DIVERGENCE = "counterfactual_divergence"
    REPEATED_ANOMALY = "repeated_anomaly"
    EXECUTIVE_CONFLICT = "executive_conflict"
    EGO_ATTRIBUTION = "ego_attribution"
    MEMORY_COMPRESSION_LOSS = "memory_compression_loss"

    ALL = (WORLD_MODEL_CONFIDENCE, PROTO_SYMBOL_AMBIGUITY,
           ANTICIPATION_MISS, WEAK_CAUSAL_CANDIDATE, MYSTERIUM,
           COUNTERFACTUAL_DIVERGENCE, REPEATED_ANOMALY, EXECUTIVE_CONFLICT,
           EGO_ATTRIBUTION, MEMORY_COMPRESSION_LOSS)


@dataclass
class UncertaintyTarget:
    """One uncertain target with its grounding source."""

    source: str
    target_ref: Optional[str] = None
    uncertainty: float = 0.0  # [0, 1]
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class UncertaintyState:
    """The aggregated uncertainty picture from one estimate."""

    targets: List[UncertaintyTarget] = field(default_factory=list)
    overall: float = 0.0
    sufficient_evidence: bool = True

    def top_targets(self, limit: int = 10) -> List[UncertaintyTarget]:
        return sorted(self.targets, key=lambda t: t.uncertainty,
                      reverse=True)[:limit]

    def top(self) -> Optional[UncertaintyTarget]:
        ranked = self.top_targets(1)
        return ranked[0] if ranked else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": round(self.overall, 4),
            "sufficient_evidence": self.sufficient_evidence,
            "target_count": len(self.targets),
            "top_targets": [t.to_dict() for t in self.top_targets(10)],
        }


@dataclass
class UncertaintyEstimator:
    """Grounds uncertainty in existing metrics; no invented targets."""

    last_state: Optional[UncertaintyState] = field(default=None, init=False)

    def estimate(self, context: Dict[str, Any]) -> UncertaintyState:
        ctx = dict(context or {})
        targets: List[UncertaintyTarget] = []
        evidence_seen = 0

        wm = ctx.get("world_model") or {}
        if wm:
            evidence_seen += 1
            accuracy = wm.get("prediction_accuracy")
            if accuracy is not None:
                targets.append(UncertaintyTarget(
                    UncertaintySource.WORLD_MODEL_CONFIDENCE,
                    "world_model", round(1.0 - float(accuracy), 4),
                    "low world-model prediction confidence"))
            low_conf = wm.get("low_confidence_nodes") or []
            if low_conf:
                targets.append(UncertaintyTarget(
                    UncertaintySource.WORLD_MODEL_CONFIDENCE,
                    str(low_conf[0]), 0.7,
                    "a specific low-confidence world-model node"))
            unknown = _num(wm, "unknown_node_count")
            nodes = _num(wm, "graph_node_count")
            if nodes > 0 and unknown > 0:
                targets.append(UncertaintyTarget(
                    UncertaintySource.WEAK_CAUSAL_CANDIDATE,
                    "unknown_region", min(1.0, unknown / nodes),
                    "unknown-to-known node ratio"))

        proto = ctx.get("proto_language") or {}
        if proto:
            evidence_seen += 1
            count = _num(proto, "symbol_count")
            ambiguous = _num(proto, "ambiguous_symbol_count")
            if count > 0:
                ratio = ambiguous / count
                if ratio > 0.0:
                    amb_list = proto.get("ambiguous_symbols") or []
                    targets.append(UncertaintyTarget(
                        UncertaintySource.PROTO_SYMBOL_AMBIGUITY,
                        str(amb_list[0]) if amb_list else "ambiguous_symbol",
                        round(min(1.0, ratio), 4),
                        "ambiguous proto-symbol grounding"))

        anticipation = ctx.get("anticipation_accuracy")
        if anticipation is not None:
            evidence_seen += 1
            targets.append(UncertaintyTarget(
                UncertaintySource.ANTICIPATION_MISS, "anticipation",
                round(1.0 - float(anticipation), 4),
                "anticipation accuracy below certainty"))

        mysterium = _num(ctx, "mysterium_pressure")
        if "mysterium_pressure" in ctx:
            evidence_seen += 1
            if mysterium > 0.0:
                targets.append(UncertaintyTarget(
                    UncertaintySource.MYSTERIUM, "unknown", mysterium,
                    "Mysterium / unknown pressure"))

        divergence = ctx.get("counterfactual_divergence")
        if divergence is not None:
            evidence_seen += 1
            if float(divergence) > 0.0:
                targets.append(UncertaintyTarget(
                    UncertaintySource.COUNTERFACTUAL_DIVERGENCE,
                    "counterfactual", round(min(1.0, float(divergence)), 4),
                    "counterfactual replay diverged"))

        ecology = ctx.get("ecology") or {}
        anomaly_rate = _num(ecology, "anomaly_rate")
        if anomaly_rate > 0.1:
            evidence_seen += 1
            targets.append(UncertaintyTarget(
                UncertaintySource.REPEATED_ANOMALY, "anomaly",
                round(min(1.0, anomaly_rate * 2.0), 4),
                "repeated ecology anomalies"))

        executive = ctx.get("executive") or {}
        if _num(executive, "no_safe_action_count") >= 3:
            evidence_seen += 1
            targets.append(UncertaintyTarget(
                UncertaintySource.EXECUTIVE_CONFLICT, "executive", 0.5,
                "repeated executive no-safe-action outcomes"))

        attribution_unknown = ctx.get("attribution_unknown_rate")
        if attribution_unknown is not None:
            evidence_seen += 1
            if float(attribution_unknown) > 0.0:
                targets.append(UncertaintyTarget(
                    UncertaintySource.EGO_ATTRIBUTION, "attribution",
                    round(min(1.0, float(attribution_unknown)), 4),
                    "ego attribution uncertainty"))

        compression_loss = ctx.get("memory_compression_loss")
        if compression_loss is not None:
            evidence_seen += 1
            if float(compression_loss) > 0.0:
                targets.append(UncertaintyTarget(
                    UncertaintySource.MEMORY_COMPRESSION_LOSS, "memory",
                    round(min(1.0, float(compression_loss)), 4),
                    "memory compression discarded detail"))

        overall = (round(sum(t.uncertainty for t in targets)
                         / len(targets), 4) if targets else 0.0)
        state = UncertaintyState(
            targets=targets, overall=overall,
            sufficient_evidence=evidence_seen > 0)
        self.last_state = state
        return state

    def top_uncertain_targets(self, limit: int = 10,
                              ) -> List[UncertaintyTarget]:
        if self.last_state is None:
            return []
        return self.last_state.top_targets(limit)

    def snapshot(self) -> Dict[str, Any]:
        if self.last_state is None:
            return {"overall": 0.0, "sufficient_evidence": False,
                    "top_targets": []}
        return self.last_state.to_dict()
