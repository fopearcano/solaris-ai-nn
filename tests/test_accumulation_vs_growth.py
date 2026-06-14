"""Post-pilot accumulation vs growth: conservative classification."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import (
    AccumulationVsGrowthAnalyzer,
    BaselineComparator,
    GrowthClassification,
)


class _Arts:
    def __init__(self, present):
        self.index = type("I", (), {"present": present})()


_FULL = ["developmental_state", "proto_symbols", "hypotheses", "observability"]


def _cmp(before, after):
    return BaselineComparator().compare_dicts("b", before, "a", after)


def test_accumulation_only_classified():
    cmp = _cmp({"proto_symbol_count": 2, "hypothesis_count": 1,
                "compression_ratio": 1.0},
               {"proto_symbol_count": 80, "hypothesis_count": 60,
                "compression_ratio": 1.0})
    result = AccumulationVsGrowthAnalyzer().analyze(cmp, [], _Arts(_FULL))
    assert result.final_classification == GrowthClassification.MOSTLY_ACCUMULATION


def test_weak_growth_conservative():
    cmp = _cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.2})
    result = AccumulationVsGrowthAnalyzer().analyze(cmp, [], _Arts(_FULL))
    assert result.final_classification == GrowthClassification.WEAK_GROWTH


def test_regression_classified():
    cmp = _cmp({"prediction_score": 0.7, "compression_ratio": 1.5,
                "ambiguous_symbol_ratio": 0.2},
               {"prediction_score": 0.3, "compression_ratio": 1.0,
                "ambiguous_symbol_ratio": 0.6})
    result = AccumulationVsGrowthAnalyzer().analyze(cmp, [], _Arts(_FULL))
    assert result.final_classification == GrowthClassification.REGRESSION


def test_missing_artifacts_inconclusive():
    cmp = _cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.2})
    result = AccumulationVsGrowthAnalyzer().analyze(cmp, [], _Arts([]))
    assert result.final_classification == GrowthClassification.INCONCLUSIVE


def test_disclaimer_present():
    cmp = _cmp({"compression_ratio": 1.0}, {"compression_ratio": 1.2})
    result = AccumulationVsGrowthAnalyzer().analyze(cmp, [], _Arts(_FULL))
    assert "not consciousness" in result.disclaimer
