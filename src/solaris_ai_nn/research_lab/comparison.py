"""Comparison engine -- full vs minimal/random/ablation, cautiously.

The :class:`ComparisonEngine` compares two runs' metric bundles, reporting per-
metric deltas, an effect direction (improved / worsened / neutral / mixed /
inconclusive), and a conservative confidence. It never claims causality from one
run, prefers the conservative interpretation, and treats a missing baseline as
inconclusive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EffectDirection:
    IMPROVED = "improved"
    WORSENED = "worsened"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    INCONCLUSIVE = "inconclusive"

    ALL = (IMPROVED, WORSENED, NEUTRAL, MIXED, INCONCLUSIVE)


class ComparisonConfidence:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    INCONCLUSIVE = "inconclusive"

    ALL = (LOW, MODERATE, HIGH, INCONCLUSIVE)


# Metrics where a lower value is the better direction.
_LOWER_IS_BETTER = frozenset({
    "ambiguity_ratio", "contradiction_count", "unresolved_tension_count",
    "stagnation_duration", "degradation_count", "repair_loop_count",
    "quarantine_count", "veto_count", "critical_failure_count",
    "claim_guard_warning_count", "esc_trigger_count", "falsified_ratio",
    "memory_growth", "drift_velocity",
})


@dataclass
class MetricDelta:
    metric: str
    baseline_value: float
    comparison_value: float

    @property
    def delta(self) -> float:
        return round(self.comparison_value - self.baseline_value, 6)

    @property
    def direction(self) -> str:
        if self.delta == 0:
            return EffectDirection.NEUTRAL
        better = (self.delta < 0) if self.metric in _LOWER_IS_BETTER \
            else (self.delta > 0)
        return EffectDirection.IMPROVED if better else EffectDirection.WORSENED

    def to_dict(self) -> Dict[str, Any]:
        return {"metric": self.metric, "baseline_value": self.baseline_value,
                "comparison_value": self.comparison_value, "delta": self.delta,
                "direction": self.direction}


@dataclass
class ComparisonResult:
    baseline_label: str
    comparison_label: str
    deltas: List[MetricDelta] = field(default_factory=list)
    effect_direction: str = EffectDirection.INCONCLUSIVE
    confidence: str = ComparisonConfidence.INCONCLUSIVE
    inconclusive: bool = False
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_label": self.baseline_label,
            "comparison_label": self.comparison_label,
            "effect_direction": self.effect_direction,
            "confidence": self.confidence, "inconclusive": self.inconclusive,
            "deltas": [d.to_dict() for d in self.deltas],
            "evidence_refs": self.evidence_refs, "limitations": self.limitations,
            "disclaimer": "Differences are observed associations from bounded "
                          "runs, not proven causal effects.",
        }


def _flatten(bundle: Dict[str, Any]) -> Dict[str, float]:
    flat: Dict[str, float] = {}
    for key, value in (bundle or {}).items():
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    flat[k] = float(v)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            flat[key] = float(value)
    return flat


@dataclass
class ComparisonEngine:
    """Compares two metric bundles cautiously; never overclaims causality."""

    def compare(self, baseline_label: str, baseline_metrics: Optional[Dict],
                comparison_label: str,
                comparison_metrics: Optional[Dict],
                run_count: int = 1) -> ComparisonResult:
        result = ComparisonResult(baseline_label=baseline_label,
                                  comparison_label=comparison_label,
                                  evidence_refs=[f"run:{baseline_label}",
                                                 f"run:{comparison_label}"])
        if baseline_metrics is None or comparison_metrics is None:
            result.inconclusive = True
            result.limitations = ["missing baseline; comparison is inconclusive"]
            return result
        base = _flatten(baseline_metrics)
        comp = _flatten(comparison_metrics)
        shared = sorted(set(base) & set(comp))
        if not shared:
            result.inconclusive = True
            result.limitations = ["no overlapping metrics; inconclusive"]
            return result
        for metric in shared:
            result.deltas.append(MetricDelta(metric, base[metric], comp[metric]))
        improved = sum(1 for d in result.deltas
                       if d.direction == EffectDirection.IMPROVED)
        worsened = sum(1 for d in result.deltas
                       if d.direction == EffectDirection.WORSENED)
        if improved and worsened:
            result.effect_direction = EffectDirection.MIXED
        elif improved:
            result.effect_direction = EffectDirection.IMPROVED
        elif worsened:
            result.effect_direction = EffectDirection.WORSENED
        else:
            result.effect_direction = EffectDirection.NEUTRAL
        # Conservative confidence: a single run is never "high".
        if run_count >= 5 and (improved == 0 or worsened == 0):
            result.confidence = ComparisonConfidence.MODERATE
        else:
            result.confidence = ComparisonConfidence.LOW
        result.limitations = [
            "single/few bounded runs; conservative interpretation",
            "no causal claim is made from this comparison",
        ]
        return result
