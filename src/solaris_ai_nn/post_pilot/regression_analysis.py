"""Post-pilot regression analysis -- did things get worse, and what to do.

The :class:`RegressionAnalyzer` detects regression signals from baseline
deltas and observation signals (prediction worsening, Mysterium saturation,
symbol explosion/ambiguity, repair loops, contradiction growth, stagnation
after early growth, ...) and recommends a conservative next step. It holds no
authority; it produces evidence and a suggestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RegressionSeverity:
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

    ALL = (NONE, LOW, MODERATE, HIGH, CRITICAL)
    _RANK = {NONE: 0, LOW: 1, MODERATE: 2, HIGH: 3, CRITICAL: 4}


class RegressionNextStep:
    CONTINUE_WITH_WATCH = "continue_with_watch"
    RUN_SHORT_DIAGNOSTIC = "run_short_diagnostic"
    ADJUST_ECOLOGY = "adjust_ecology"
    INCREASE_CONSOLIDATION = "increase_consolidation"
    REDUCE_ACTIVE_SAMPLING = "reduce_active_sampling"
    RUN_AUTOREGENERATION = "run_autoregeneration"
    PAUSE_AND_REVIEW = "pause_and_review"
    ARCHITECTURE_REVISION_REQUIRED = "architecture_revision_required"

    ALL = (CONTINUE_WITH_WATCH, RUN_SHORT_DIAGNOSTIC, ADJUST_ECOLOGY,
           INCREASE_CONSOLIDATION, REDUCE_ACTIVE_SAMPLING,
           RUN_AUTOREGENERATION, PAUSE_AND_REVIEW,
           ARCHITECTURE_REVISION_REQUIRED)


@dataclass
class RegressionSignal:
    """One detected regression with its probable cause and suggested step."""

    name: str
    severity: str
    probable_cause: str = ""
    suggested_next_step: str = RegressionNextStep.CONTINUE_WITH_WATCH
    metric_delta: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RegressionReport:
    """The aggregate regression picture."""

    signals: List[RegressionSignal] = field(default_factory=list)
    overall_severity: str = RegressionSeverity.NONE
    suggested_next_step: str = RegressionNextStep.CONTINUE_WITH_WATCH

    @property
    def regression_score(self) -> float:
        return round(sum(RegressionSeverity._RANK.get(s.severity, 0)
                         for s in self.signals) / 4.0, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {"signals": [s.to_dict() for s in self.signals],
                "overall_severity": self.overall_severity,
                "suggested_next_step": self.suggested_next_step,
                "regression_score": self.regression_score}


@dataclass
class RegressionAnalyzer:
    """Detects regression and recommends a conservative next step."""

    def analyze(self, comparison: Any = None,
                signals: Optional[Dict[str, Any]] = None) -> RegressionReport:
        deltas = getattr(comparison, "deltas", {}) or {}
        signals = dict(signals or {})
        report = RegressionReport()
        S = RegressionSeverity
        N = RegressionNextStep

        def d(key: str) -> float:
            return float(deltas.get(key, 0.0) or 0.0)

        def flag(name: str, cond: bool, severity: str, cause: str,
                 step: str, delta: float = 0.0) -> None:
            if cond:
                report.signals.append(RegressionSignal(
                    name=name, severity=severity, probable_cause=cause,
                    suggested_next_step=step, metric_delta=delta))

        flag("prediction_worsening", d("prediction_score") < 0, S.MODERATE,
             "readout is fitting noise or the world shifted",
             N.RUN_SHORT_DIAGNOSTIC, d("prediction_score"))
        flag("mysterium_saturation",
             float(signals.get("mysterium_pressure", 0.0) or 0.0) >= 0.95
             or d("mysterium_pressure") > 0.3, S.MODERATE,
             "novelty pressure not being resolved", N.INCREASE_CONSOLIDATION,
             d("mysterium_pressure"))
        flag("memory_compression_collapse", d("compression_ratio") < 0,
             S.HIGH, "consolidation is failing or being bypassed",
             N.INCREASE_CONSOLIDATION, d("compression_ratio"))
        flag("symbol_explosion", d("proto_symbol_count") > 200, S.MODERATE,
             "symbols created faster than they stabilize",
             N.ADJUST_ECOLOGY, d("proto_symbol_count"))
        flag("symbol_ambiguity_increase", d("ambiguous_symbol_ratio") > 0,
             S.MODERATE, "symbols losing distinct grounding",
             N.ADJUST_ECOLOGY, d("ambiguous_symbol_ratio"))
        flag("hypothesis_inconclusive_loop",
             bool(signals.get("inconclusive_hypothesis_loop")), S.LOW,
             "tests not discriminating", N.RUN_SHORT_DIAGNOSTIC)
        flag("active_perception_harmful",
             d("active_perception_sampling_count") > 0
             and d("active_perception_usefulness") < 0, S.MODERATE,
             "sampling adding noise, not information",
             N.REDUCE_ACTIVE_SAMPLING,
             d("active_perception_usefulness"))
        flag("logos_overload", bool(signals.get("logos_overloaded")),
             S.MODERATE, "too many unresolved tensions",
             N.INCREASE_CONSOLIDATION)
        flag("autoregeneration_repair_loop",
             bool(signals.get("repair_loop")), S.HIGH,
             "repairs recurring without fixing the cause",
             N.RUN_AUTOREGENERATION)
        flag("degraded_module_recurrence",
             bool(signals.get("degraded_module_recurrence")), S.HIGH,
             "a module keeps failing", N.PAUSE_AND_REVIEW)
        flag("identity_continuity_weakening",
             not getattr(comparison, "identity_continuous", True), S.CRITICAL,
             "restart did not preserve identity",
             N.ARCHITECTURE_REVISION_REQUIRED)
        flag("checkpoint_decline", bool(signals.get("checkpoint_decline")),
             S.HIGH, "checkpoint reliability dropping", N.PAUSE_AND_REVIEW)
        flag("world_model_contradiction_increase",
             d("world_model_contradiction_count") > 0, S.MODERATE,
             "contradictions accumulating unresolved",
             N.RUN_SHORT_DIAGNOSTIC, d("world_model_contradiction_count"))
        flag("stagnation_after_growth",
             bool(signals.get("stagnation_after_growth"))
             or d("stagnation_seconds") > 7 * 86400.0, S.MODERATE,
             "early movement then flat", N.ADJUST_ECOLOGY,
             d("stagnation_seconds"))

        report.overall_severity = self._overall(report.signals)
        report.suggested_next_step = self._strongest_step(report.signals)
        return report

    @staticmethod
    def _overall(signals: List[RegressionSignal]) -> str:
        if not signals:
            return RegressionSeverity.NONE
        return max(signals,
                   key=lambda s: RegressionSeverity._RANK.get(s.severity, 0)
                   ).severity

    @staticmethod
    def _strongest_step(signals: List[RegressionSignal]) -> str:
        order = list(RegressionNextStep.ALL)
        if not signals:
            return RegressionNextStep.CONTINUE_WITH_WATCH
        return max((s.suggested_next_step for s in signals),
                   key=lambda step: order.index(step)
                   if step in order else 0)
