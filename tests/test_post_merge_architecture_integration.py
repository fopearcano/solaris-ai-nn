"""Post-merge sends module status + evidence bundle to Architecture Evolution."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime


def _runtime(tmp_path, blocked=False):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    intake = ({"merge_recommendation_status": "block_merge_due_to_safety",
               "critical_safety_regression_count": 2,
               "forbidden_file_change_count": 1} if blocked else
              {"merge_recommendation_status": "recommend_merge",
               "critical_safety_regression_count": 0,
               "spec_compliance_status": "satisfied", "test_failure_count": 0})
    validation = ({"full_test_run": {"passed": False}} if blocked else
                  {"full_test_run": {"passed": True},
                   "safety_invariant_run": {"passed": True},
                   "claimguard_run": {"safe": True}, "mini_soak": {"passed": True}})
    rt.load_bundle({
        "merge_manifest": {"merge_id": "m1",
                           "confirmation": {"confirmed_by_operator": True}},
        "implementation_intake": intake, "validation_results": validation,
        "parent_metrics": {"sensorium_metrics": 0.5},
        "candidate_metrics": {"sensorium_metrics": 0.6}})
    rt.run()
    return rt


def test_sends_module_status_recommendations(tmp_path):
    rt = _runtime(tmp_path)
    evidence = rt.architecture_evidence()
    assert "module_status_recommendation" in evidence
    assert evidence["module_status_recommendation"]["update_type"]


def test_sends_evidence_assimilation_bundle(tmp_path):
    rt = _runtime(tmp_path)
    evidence = rt.architecture_evidence()
    assert "evidence_assimilation_bundle" in evidence
    assert "baseline_record" in evidence
    assert "regression_watch" in evidence
    assert "rollback_watch" in evidence
    assert "followup_queue" in evidence


def test_blocked_baseline_record_carries_blockers(tmp_path):
    rt = _runtime(tmp_path, blocked=True)
    evidence = rt.architecture_evidence()
    assert evidence["baseline_record"]["unresolved_blockers"]
