"""The cycle tracker never approves itself or invents operator approval."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import (
    DecisionGateStatus,
    DecisionGateType,
    ResearchCycleDecisionGate,
    ResearchCycleRuntime,
    required_decisions,
    load_operator_decisions,
)


def test_operator_gate_never_auto_passes_without_decision():
    bundle = {"research_baseline": {"baseline_status": "validated",
                                    "safety_boundary_status": "pass"},
              "implementation_intake": {"merge_recommendation_status":
                                        "recommend"},
              "post_merge": {"candidate_baseline_status": "validated",
                             "critical_regression_count": 0}}
    gate = ResearchCycleDecisionGate()
    res = {r.gate_type: r for r in gate.evaluate_all(bundle,
                                                     operator_decisions=[])}
    # No operator decision -> these MUST wait, not pass.
    assert res[DecisionGateType.MERGE_READINESS].status == \
        DecisionGateStatus.WAITING_FOR_OPERATOR
    assert res[DecisionGateType.RESEARCH_BASELINE].status == \
        DecisionGateStatus.WAITING_FOR_OPERATOR


def test_required_decisions_remain_until_operator_acts():
    bundle = {"post_merge": {"x": 1}, "experiment_compiler": {"x": 1}}
    assert required_decisions(bundle, load_operator_decisions([])) != []


def test_runtime_status_reports_not_self_approving(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle({"research_baseline": {"baseline_status": "validated"},
                    "post_merge": {"candidate_baseline_status": "validated"}})
    rt.run()
    assert rt.research_cycle_status()["approves_itself"] is False
