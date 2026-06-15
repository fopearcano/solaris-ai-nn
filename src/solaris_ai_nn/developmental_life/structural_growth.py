"""Structural growth analysis -- distinguish real growth from mere accumulation.

The :class:`StructuralGrowthAnalyzer` decides, conservatively, whether the
developmental record shows *real structural growth* or merely event accumulation /
log bloat / fixture or human-label overfit / random fluctuation / regression. A
negative or inconclusive result is valid; growth is never over-claimed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class GrowthVerdict:
    STRUCTURAL_GROWTH = "real_structural_growth"
    EVENT_ACCUMULATION = "mere_event_accumulation"
    LOG_BLOAT = "log_bloat"
    FIXTURE_OVERFIT = "fixture_overfit"
    HUMAN_LABEL_OVERFIT = "human_label_overfit"
    RANDOM_FLUCTUATION = "random_fluctuation"
    TEMPORARY_SPIKE = "temporary_spike"
    REGRESSION = "regression"
    INCONCLUSIVE = "inconclusive"

    ALL = (STRUCTURAL_GROWTH, EVENT_ACCUMULATION, LOG_BLOAT, FIXTURE_OVERFIT,
           HUMAN_LABEL_OVERFIT, RANDOM_FLUCTUATION, TEMPORARY_SPIKE,
           REGRESSION, INCONCLUSIVE)


@dataclass
class GrowthVsAccumulationResult:
    verdict: str
    structural_growth_score: float
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"verdict": self.verdict,
                "structural_growth_score": round(self.structural_growth_score,
                                                 4),
                "evidence": list(self.evidence),
                "warnings": list(self.warnings),
                "note": "conservative; negative/inconclusive results are valid "
                        "and growth is never over-claimed"}


@dataclass
class StructuralGrowthReport:
    result: GrowthVsAccumulationResult
    durable_prediction_improvement: float = 0.0
    durable_action_effect_learning: float = 0.0
    durable_concept_stability: float = 0.0
    durable_sign_stability: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result.to_dict(),
            "durable_prediction_improvement": round(
                self.durable_prediction_improvement, 4),
            "durable_action_effect_learning": round(
                self.durable_action_effect_learning, 4),
            "durable_concept_stability": round(
                self.durable_concept_stability, 4),
            "durable_sign_stability": round(self.durable_sign_stability, 4),
        }


def _durable(history: List[float], dim: str) -> float:
    """Min over the second half of the history (a value that 'held')."""
    vals = [h.get(dim, 0.0) for h in history] if history else []
    if not vals:
        return 0.0
    half = vals[len(vals) // 2:]
    return round(min(half), 4) if half else 0.0


@dataclass
class StructuralGrowthAnalyzer:
    """Conservatively classifies growth vs accumulation from the history."""

    def analyze(self, *, dim_history: List[Dict[str, float]],
                statuses: Dict[str, Dict[str, Any]],
                regression_count: int = 0,
                accumulation_warnings: int = 0) -> StructuralGrowthReport:
        evidence: List[str] = []
        warnings: List[str] = []

        durable_pred = _durable(dim_history, "prediction_skill")
        durable_action = _durable(dim_history, "action_effect_learning")
        durable_concept = _durable(dim_history, "concept_stability")
        durable_sign = _durable(dim_history, "sign_growth")
        contamination_resist = _durable(dim_history, "contamination_resistance")

        if durable_pred >= 0.3:
            evidence.append("durable prediction improvement")
        if durable_action >= 0.2:
            evidence.append("durable action-effect learning")
        if durable_concept >= 0.3:
            evidence.append("durable concept stability")
        if durable_sign >= 0.2:
            evidence.append("durable sign utility")
        if contamination_resist >= 0.6:
            evidence.append("lower contamination")

        # Fixture / label overfit checks.
        sb = statuses.get("self_boundary", {})
        if not sb.get("live_grounded", False) and durable_concept >= 0.5:
            warnings.append("fixture-only stability (possible fixture overfit)")
        sem = statuses.get("semiogenesis", {})
        if float(sem.get("gloss_dependence_score", 0.0) or 0.0) >= 0.5:
            warnings.append("high gloss dependence (possible human-label "
                            "overfit)")

        score = round(min(1.0, 0.25 * len(evidence)), 4)

        if regression_count > len(evidence):
            verdict = GrowthVerdict.REGRESSION
        elif len(evidence) >= 3 and not warnings:
            verdict = GrowthVerdict.STRUCTURAL_GROWTH
        elif "fixture-only stability (possible fixture overfit)" in warnings:
            verdict = GrowthVerdict.FIXTURE_OVERFIT
        elif any("human-label overfit" in w for w in warnings):
            verdict = GrowthVerdict.HUMAN_LABEL_OVERFIT
        elif accumulation_warnings > 0 and not evidence:
            verdict = GrowthVerdict.EVENT_ACCUMULATION
        elif not evidence:
            verdict = GrowthVerdict.INCONCLUSIVE
        else:
            verdict = GrowthVerdict.INCONCLUSIVE

        return StructuralGrowthReport(
            result=GrowthVsAccumulationResult(
                verdict=verdict, structural_growth_score=score,
                evidence=evidence, warnings=warnings),
            durable_prediction_improvement=durable_pred,
            durable_action_effect_learning=durable_action,
            durable_concept_stability=durable_concept,
            durable_sign_stability=durable_sign)
