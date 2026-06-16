"""Research baseline consumes intake: safety regression -> limitation, coverage."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import ResearchBaselineRuntime


def _run(tmp_path, intake):
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1")
    rt.load_bundle({
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0,
                       "rollback_recommendation_status": "no_rollback_needed",
                       "unresolved_blockers": []},
        "implementation_intake": intake,
        "validation_results": {"unit_tests": {"passed": True},
                               "safety_tests": {"passed": True},
                               "claimguard": {"safe": True},
                               "safety_invariants": {"passed": True}},
        "safety_artifacts": {"passed": True},
        "snapshot_artifacts": {"evaluation_report": {"payload": {"e": 1}}}})
    rt.run()
    return rt


def test_consumes_intake_report(tmp_path):
    rt = _run(tmp_path, {"critical_safety_regression_count": 0,
                        "coverage_gap_count": 0,
                        "spec_compliance_status": "satisfied"})
    assert rt.limitations is not None


def test_safety_regression_affects_limitation_registry(tmp_path):
    rt = _run(tmp_path, {"critical_safety_regression_count": 1,
                        "coverage_gap_count": 0})
    cats = {l["category"] for l in rt.limitations["limitations"]}
    assert "weak_safety_evidence" in cats
    assert rt.limitations["critical_limitation_count"] >= 1
    # A critical safety limitation blocks validation.
    assert rt.version.validated is False


def test_coverage_gap_affects_limitations(tmp_path):
    rt = _run(tmp_path, {"critical_safety_regression_count": 0,
                        "coverage_gap_count": 3})
    cats = {l["category"] for l in rt.limitations["limitations"]}
    assert "missing_evidence" in cats
