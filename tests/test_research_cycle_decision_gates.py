"""Decision gates: advisory; safety/falsification block; no auto-approval."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import (
    DecisionGateStatus,
    DecisionGateType,
    ResearchCycleDecisionGate,
)


def _bundle(safety_ok=True, falsified=0):
    return {
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "experiment_compiler": {"ready_spec_count": 2,
                                "safety_gate_failure_count": 0},
        "implementation_intake": {
            "merge_recommendation_status":
                "recommend" if safety_ok else "block_merge_due_to_safety",
            "critical_safety_regression_count": 0 if safety_ok else 1},
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0},
        "falsification": {"falsified_claim_count": falsified},
    }


def _by_type(results):
    return {r.gate_type: r for r in results}


def test_operator_gate_waits_without_decision():
    gate = ResearchCycleDecisionGate()
    res = _by_type(gate.evaluate_all(_bundle(), operator_decisions=[]))
    assert res[DecisionGateType.MERGE_READINESS].status == \
        DecisionGateStatus.WAITING_FOR_OPERATOR
    assert res[DecisionGateType.MERGE_READINESS].operator_decision_required


def test_operator_gate_passes_with_decision():
    gate = ResearchCycleDecisionGate()
    res = _by_type(gate.evaluate_all(_bundle(), operator_decisions=[
        {"decision_type": "confirm_external_merge", "status": "approved"}]))
    assert res[DecisionGateType.MERGE_READINESS].passed


def test_safety_blocks_promotion_gates():
    gate = ResearchCycleDecisionGate()
    res = _by_type(gate.evaluate_all(_bundle(safety_ok=False),
                                     operator_decisions=[]))
    assert res[DecisionGateType.RESEARCH_BASELINE].status == \
        DecisionGateStatus.BLOCKED_BY_SAFETY


def test_falsification_blocks_promotion_gates():
    gate = ResearchCycleDecisionGate()
    res = _by_type(gate.evaluate_all(_bundle(falsified=1), operator_decisions=[]))
    assert res[DecisionGateType.NEXT_CYCLE].status == \
        DecisionGateStatus.BLOCKED_BY_FALSIFICATION


def test_summary_advisory_and_counts():
    gate = ResearchCycleDecisionGate()
    summary = gate.summary(gate.evaluate_all(_bundle(safety_ok=False)))
    assert summary["failed_decision_gate_count"] >= 1
    assert summary["all_critical_passed"] is False
    assert all(r["advisory"] is True for r in summary["results"])
