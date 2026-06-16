"""Research baseline consumes post-merge; rollback/critical regression block."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import ResearchBaselineRuntime


def _run(tmp_path, post_merge, validation=None, safety=True):
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1")
    rt.load_bundle({
        "post_merge": post_merge,
        "implementation_intake": {"critical_safety_regression_count":
                                  post_merge.get("critical_regression_count", 0),
                                  "spec_compliance_status": "satisfied"},
        "validation_results": validation or {
            "unit_tests": {"passed": True}, "safety_tests": {"passed": True},
            "claimguard": {"safe": True}, "safety_invariants": {"passed": True}},
        "safety_artifacts": {"passed": safety},
        "snapshot_artifacts": {"evaluation_report": {"payload": {"e": 1}}}})
    rt.run()
    return rt


def test_consumes_post_merge_registry(tmp_path):
    rt = _run(tmp_path, {"candidate_baseline_status": "validated",
                        "critical_regression_count": 0,
                        "rollback_recommendation_status": "no_rollback_needed",
                        "unresolved_blockers": []})
    assert rt.version is not None
    assert rt.version.candidate_baseline_id == ""  # not supplied
    assert rt.version.status in ("validated", "validated_with_warnings")


def test_rollback_recommendation_blocks_validation(tmp_path):
    rt = _run(tmp_path, {"candidate_baseline_status": "rollback_recommended",
                        "critical_regression_count": 0,
                        "rollback_recommendation_status": "rollback_recommended",
                        "unresolved_blockers": ["rollback"]})
    assert rt.version.blocked is True
    assert rt.version.validated is False


def test_critical_regression_blocks_validation(tmp_path):
    rt = _run(tmp_path, {"candidate_baseline_status": "validated",
                        "critical_regression_count": 2,
                        "rollback_recommendation_status": "no_rollback_needed",
                        "unresolved_blockers": []})
    # Critical regression -> critical limitation -> blocked, not validated.
    assert rt.version.validated is False
