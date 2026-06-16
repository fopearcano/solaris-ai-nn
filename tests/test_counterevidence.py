"""Counterevidence: failed replication, fixture overfit, visibility, blocking."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    CounterEvidenceAnalyzer,
    CounterEvidenceType,
)


def test_failed_replication_detected():
    recs = CounterEvidenceAnalyzer().detect({
        "replication": {"failed_replication_count": 2}})
    assert any(r.counter_type == CounterEvidenceType.FAILED_REPLICATION
               for r in recs)


def test_fixture_overfit_detected():
    recs = CounterEvidenceAnalyzer().detect({"fixture_overfit_risk": True})
    assert any(r.counter_type == CounterEvidenceType.FIXTURE_OVERFIT
               for r in recs)


def test_passive_parser_and_missing_live():
    recs = CounterEvidenceAnalyzer().detect({
        "passive_parser_equivalent": True, "missing_live_data": True})
    types = {r.counter_type for r in recs}
    assert CounterEvidenceType.PASSIVE_PARSER_EQUIVALENCE in types
    assert CounterEvidenceType.MISSING_LIVE_DATA in types


def test_counterevidence_visible_and_blocking():
    recs = CounterEvidenceAnalyzer().detect({
        "falsification": {"falsified_claim_count": 1}})
    summary = CounterEvidenceAnalyzer.summary(recs)
    assert summary["counterevidence_count"] >= 1
    assert summary["blocking_counterevidence_count"] >= 1
    assert all(r["visible"] is True and r["ignored"] is False
               for r in summary["records"])


def test_safety_regression_blocks():
    recs = CounterEvidenceAnalyzer().detect({
        "safety": {"critical_regression_count": 1}})
    rec = [r for r in recs
           if r.counter_type == CounterEvidenceType.SAFETY_REGRESSION][0]
    assert rec.blocks_claim is True
