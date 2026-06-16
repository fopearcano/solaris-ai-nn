"""Post-merge consumes intake report; blocked-safety stays blocked; advisory."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime


def _run(tmp_path, intake, validation):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    rt.load_bundle({
        "merge_manifest": {"merge_id": "m1",
                           "confirmation": {"confirmed_by_operator": True}},
        "implementation_intake": intake, "validation_results": validation,
        "parent_metrics": {"sensorium_metrics": 0.5},
        "candidate_metrics": {"sensorium_metrics": 0.6}})
    rt.run()
    return rt


def test_consumes_intake_report(tmp_path):
    rt = _run(tmp_path, {"merge_recommendation_status": "recommend_merge",
                        "critical_safety_regression_count": 0,
                        "spec_compliance_status": "satisfied",
                        "test_failure_count": 0},
              {"full_test_run": {"passed": True},
               "safety_invariant_run": {"passed": True},
               "claimguard_run": {"safe": True}})
    # The intake recommendation is assimilated as advisory evidence.
    sources = {f["source"] for f in rt.evidence["findings"]}
    assert "intake_merge_recommendation" in sources


def test_blocked_intake_prevents_validation_without_new_safety_evidence(
        tmp_path):
    # Intake blocked by safety and NO passing safety_invariant_run supplied.
    rt = _run(tmp_path,
              {"merge_recommendation_status": "block_merge_due_to_safety",
               "critical_safety_regression_count": 2},
              {"full_test_run": {"passed": True}})  # safety_invariant missing
    assert rt.candidate.status == "blocked_by_safety"


def test_blocked_intake_can_clear_with_passing_safety_evidence(tmp_path):
    # Operator supplies a separate passing safety invariant run; the safety
    # block from intake can clear only because the new safety evidence passes.
    rt = _run(tmp_path,
              {"merge_recommendation_status": "block_merge_due_to_safety",
               "critical_safety_regression_count": 0,
               "spec_compliance_status": "satisfied", "test_failure_count": 0},
              {"full_test_run": {"passed": True},
               "safety_invariant_run": {"passed": True},
               "claimguard_run": {"safe": True}, "mini_soak": {"passed": True}})
    assert rt.candidate.status != "blocked_by_safety"


def test_intake_recommendation_preserved_as_advisory(tmp_path):
    rt = _run(tmp_path, {"merge_recommendation_status": "recommend_merge",
                        "critical_safety_regression_count": 0,
                        "spec_compliance_status": "satisfied",
                        "test_failure_count": 0},
              {"full_test_run": {"passed": True},
               "safety_invariant_run": {"passed": True},
               "claimguard_run": {"safe": True}})
    rec = next(f for f in rt.evidence["findings"]
               if f["source"] == "intake_merge_recommendation")
    assert "recommend_merge" in rec["detail"]
