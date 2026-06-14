"""Post-pilot accumulation-vs-growth discrimination.

The :class:`AccumulationVsGrowthAnalyzer` scores signals of *accumulation*
(counts rising without payoff) against signals of *growth* (durable, useful
structural change) and returns a conservative classification. It never calls
the result consciousness, never overstates "strong growth", and returns
``inconclusive`` when the artifacts needed to judge are missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class GrowthClassification:
    MOSTLY_ACCUMULATION = "mostly_accumulation"
    WEAK_GROWTH = "weak_growth_evidence"
    MODERATE_GROWTH = "moderate_growth_evidence"
    STRONG_GROWTH = "strong_growth_evidence"
    REGRESSION = "regression"
    INCONCLUSIVE = "inconclusive"

    ALL = (MOSTLY_ACCUMULATION, WEAK_GROWTH, MODERATE_GROWTH, STRONG_GROWTH,
           REGRESSION, INCONCLUSIVE)


@dataclass
class GrowthDiscriminationResult:
    """The accumulation/growth scores and final conservative classification."""

    accumulation_score: float = 0.0
    growth_score: float = 0.0
    mixed_score: float = 0.0
    unknown_score: float = 0.0
    final_classification: str = GrowthClassification.INCONCLUSIVE
    accumulation_signals: List[str] = field(default_factory=list)
    growth_signals: List[str] = field(default_factory=list)
    regression_signals: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    disclaimer: str = ("Growth here means durable, useful structural change in "
                       "a software process. It is not consciousness, "
                       "understanding, or life.")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AccumulationVsGrowthAnalyzer:
    """Weighs accumulation vs growth signals from comparison + evidence."""

    def analyze(self, comparison: Any = None,
                structural_evidence: Optional[List[Any]] = None,
                artifacts: Any = None,
                signals: Optional[Dict[str, Any]] = None,
                ) -> GrowthDiscriminationResult:
        deltas = getattr(comparison, "deltas", {}) or {}
        signals = dict(signals or {})
        result = GrowthDiscriminationResult()
        present = set(getattr(getattr(artifacts, "index", None), "present", [])
                     or [])

        acc = result.accumulation_signals
        grow = result.growth_signals
        reg = result.regression_signals

        def d(key: str) -> float:
            return float(deltas.get(key, 0.0) or 0.0)

        # -- accumulation signals --
        if d("proto_symbol_count") > 0 and d("ambiguous_symbol_ratio") >= 0:
            acc.append("symbol count rose without ambiguity falling")
        if d("hypothesis_count") > 0 and d("supported_hypothesis_count") <= 0:
            acc.append("hypotheses grew without more support")
        if d("world_model_edge_count") > 0 and d("prediction_score") <= 0:
            acc.append("world-model edges grew without prediction gain")
        if d("logos_tension_count") > 0 and d("resolved_tension_count") <= 0:
            acc.append("tensions rose without resolution")
        if d("active_perception_sampling_count") > 0 and \
                d("active_perception_usefulness") <= 0:
            acc.append("sampling rose without useful results")
        if d("autoregeneration_event_count") > 0 and \
                d("world_model_contradiction_count") >= 0:
            acc.append("repeated repairs without reduced degradation")
        if d("memory_layer_count") > 0 and d("compression_ratio") <= 0:
            acc.append("memory grew without compression")
        if signals.get("raw_log_growth_only"):
            acc.append("raw log growth only")

        # -- growth signals --
        if d("compression_ratio") > 0:
            grow.append("compression improved (schema consolidation)")
        if d("ambiguous_symbol_ratio") < 0:
            grow.append("symbol ambiguity fell")
        if d("prediction_score") > 0:
            grow.append("prediction improved after experience")
        if d("supported_hypothesis_count") > 0:
            grow.append("more hypotheses earned support")
        if d("world_model_contradiction_count") < 0:
            grow.append("fewer world-model contradictions")
        if d("resolved_tension_count") > 0:
            grow.append("LOGOS tensions resolved")
        if d("active_perception_usefulness") > 0:
            grow.append("active sampling became more useful")
        if d("habit_stability") > 0:
            grow.append("habits stabilized")
        if d("structural_change_score") > 0:
            grow.append("structural-change score rose")

        # -- regression signals --
        if d("prediction_score") < 0:
            reg.append("prediction worsened")
        if d("ambiguous_symbol_ratio") > 0:
            reg.append("symbol ambiguity rose")
        if d("world_model_contradiction_count") > 0:
            reg.append("contradictions increased")
        if d("compression_ratio") < 0:
            reg.append("compression collapsed")
        if d("safety_incident_count") > 0:
            reg.append("safety incidents increased")

        # Persistent, corroborated structural evidence strengthens growth.
        evidence = structural_evidence or []
        persistent = sum(1 for e in evidence
                         if getattr(e, "stability", "") == "persistent")
        high_conf = sum(1 for e in evidence
                        if getattr(e, "confidence", 0.0) >= 0.6)

        result.accumulation_score = round(float(len(acc)), 4)
        result.growth_score = round(
            len(grow) + 0.5 * persistent + 0.25 * high_conf, 4)
        result.mixed_score = round(min(len(acc), len(grow)), 4)
        # Unknown score rises when key artifacts are absent.
        needed = {"developmental_state", "proto_symbols", "hypotheses",
                  "observability"}
        result.unknown_score = round(float(len(needed - present)), 4)

        result.final_classification = self._classify(result, reg, present,
                                                     persistent)
        result.limitations = self._limitations(present)
        return result

    def _classify(self, r: GrowthDiscriminationResult, reg: List[str],
                  present: set, persistent: int) -> str:
        # Missing the core artifacts -> we cannot judge.
        if r.unknown_score >= 3:
            return GrowthClassification.INCONCLUSIVE
        if len(reg) >= 2 and r.growth_score <= r.accumulation_score:
            return GrowthClassification.REGRESSION
        if r.growth_score == 0 and r.accumulation_score == 0:
            return GrowthClassification.INCONCLUSIVE
        if r.accumulation_score > r.growth_score:
            return GrowthClassification.MOSTLY_ACCUMULATION
        # Growth ahead of accumulation -> grade conservatively.
        margin = r.growth_score - r.accumulation_score
        if persistent >= 2 and margin >= 3:
            return GrowthClassification.STRONG_GROWTH
        if margin >= 2:
            return GrowthClassification.MODERATE_GROWTH
        return GrowthClassification.WEAK_GROWTH

    @staticmethod
    def _limitations(present: set) -> List[str]:
        lims = ["Classification is conservative; 'growth' is operational, not "
                "cognitive."]
        for needed in ("developmental_state", "proto_symbols", "hypotheses",
                       "observability"):
            if needed not in present:
                lims.append(f"missing artifact weakens the result: {needed}")
        return lims
