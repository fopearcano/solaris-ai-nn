"""Post-pilot regression analysis: detection, severity, next steps."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import (
    BaselineComparator,
    RegressionAnalyzer,
    RegressionSeverity,
)


def _cmp(before, after):
    return BaselineComparator().compare_dicts("b", before, "a", after)


def test_symbol_explosion_detected():
    cmp = _cmp({"proto_symbol_count": 2}, {"proto_symbol_count": 400})
    report = RegressionAnalyzer().analyze(cmp)
    assert any(s.name == "symbol_explosion" for s in report.signals)


def test_mysterium_saturation_detected():
    report = RegressionAnalyzer().analyze(
        None, signals={"mysterium_pressure": 0.97})
    assert any(s.name == "mysterium_saturation" for s in report.signals)


def test_checkpoint_decline_detected():
    report = RegressionAnalyzer().analyze(
        None, signals={"checkpoint_decline": True})
    names = {s.name for s in report.signals}
    assert "checkpoint_decline" in names


def test_compression_collapse_high_severity():
    cmp = _cmp({"compression_ratio": 1.5}, {"compression_ratio": 1.0})
    report = RegressionAnalyzer().analyze(cmp)
    sig = [s for s in report.signals if s.name == "memory_compression_collapse"]
    assert sig and sig[0].severity == RegressionSeverity.HIGH


def test_no_regression_is_none():
    cmp = _cmp({"prediction_score": 0.5}, {"prediction_score": 0.6})
    report = RegressionAnalyzer().analyze(cmp)
    assert report.overall_severity == RegressionSeverity.NONE


def test_next_step_recommended():
    cmp = _cmp({"prediction_score": 0.7}, {"prediction_score": 0.3})
    report = RegressionAnalyzer().analyze(cmp)
    assert report.suggested_next_step
    assert report.regression_score >= 0.0
