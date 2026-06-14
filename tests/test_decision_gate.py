"""Post-pilot Phase-2 decision gate: readiness, repeat, revise."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import (
    DecisionOption,
    GrowthClassification,
    Phase2DecisionGate,
    RegressionReport,
    RegressionSeverity,
)
from solaris_ai_nn.post_pilot.accumulation_vs_growth import (
    GrowthDiscriminationResult,
)
from solaris_ai_nn.post_pilot.trace_audit import TraceAuditResult


def _growth(cls):
    return GrowthDiscriminationResult(final_classification=cls)


def _exit(success):
    return type("E", (), {"success": success})()


def test_ready_for_pilot2_requires_safety_and_analyzability():
    gate = Phase2DecisionGate()
    result = gate.decide(
        exit_decision=_exit(True),
        growth=_growth(GrowthClassification.MODERATE_GROWTH),
        regression=RegressionReport(),
        trace_audit=TraceAuditResult(traceability_score=0.9))
    assert result.recommendation == DecisionOption.READY_FOR_PILOT2

    # A safety incident blocks readiness.
    blocked = gate.decide(
        exit_decision=_exit(True),
        growth=_growth(GrowthClassification.MODERATE_GROWTH),
        regression=RegressionReport(),
        trace_audit=TraceAuditResult(traceability_score=0.9),
        safety_incident_count=1)
    assert blocked.recommendation != DecisionOption.READY_FOR_PILOT2
    assert blocked.blockers


def test_repeat_pilot1_on_inconclusive():
    result = Phase2DecisionGate().decide(
        exit_decision=_exit(False),
        growth=_growth(GrowthClassification.INCONCLUSIVE),
        regression=RegressionReport(),
        trace_audit=TraceAuditResult(traceability_score=0.7))
    assert result.recommendation == DecisionOption.REPEAT_PILOT1


def test_architecture_revision_on_severe_regression():
    result = Phase2DecisionGate().decide(
        growth=_growth(GrowthClassification.REGRESSION),
        regression=RegressionReport(
            overall_severity=RegressionSeverity.CRITICAL),
        trace_audit=TraceAuditResult(traceability_score=0.6))
    assert result.recommendation == DecisionOption.REVISE_ARCHITECTURE


def test_not_analyzable_blocks_readiness():
    result = Phase2DecisionGate().decide(
        exit_decision=_exit(True),
        growth=_growth(GrowthClassification.MODERATE_GROWTH),
        regression=RegressionReport(),
        trace_audit=TraceAuditResult(traceability_score=0.2))
    assert result.recommendation != DecisionOption.READY_FOR_PILOT2
    assert any("analyzable" in b for b in result.blockers)


def test_result_has_rationale_and_limitations():
    result = Phase2DecisionGate().decide(
        growth=_growth(GrowthClassification.MOSTLY_ACCUMULATION),
        regression=RegressionReport(),
        trace_audit=TraceAuditResult(traceability_score=0.8))
    assert result.rationale and result.limitations
