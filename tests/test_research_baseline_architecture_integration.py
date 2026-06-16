"""Research baseline exports a clean starting point to architecture evolution."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import ResearchBaselineRuntime


def _runtime(tmp_path, missing_replication=False):
    snapshot = {"evaluation_report": {"payload": {"e": 1}}}
    if not missing_replication:
        snapshot["replication_report"] = {"payload": {"r": 1}}
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1",
                                 parent_baseline_id="b1")
    rt.load_bundle({
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0,
                       "rollback_recommendation_status": "no_rollback_needed",
                       "unresolved_blockers": []},
        "implementation_intake": {"critical_safety_regression_count": 0,
                                  "spec_compliance_status": "satisfied"},
        "validation_results": {"unit_tests": {"passed": True},
                               "safety_tests": {"passed": True},
                               "claimguard": {"safe": True},
                               "safety_invariants": {"passed": True}},
        "safety_artifacts": {"passed": True},
        "snapshot_artifacts": snapshot,
        "available_anchors": {"parent_baseline": "b1"}})
    rt.run()
    return rt


def test_exports_clean_starting_point(tmp_path):
    rt = _runtime(tmp_path)
    sp = rt.architecture_starting_point()
    assert "research_baseline_version" in sp
    assert "capability_map" in sp
    assert "limitation_registry" in sp
    assert "next_cycle_roadmap" in sp
    assert "comparison_anchors" in sp
    assert "missing_evidence" in sp


def test_missing_evidence_preserved(tmp_path):
    rt = _runtime(tmp_path, missing_replication=True)
    sp = rt.architecture_starting_point()
    assert "replication_report" in sp["missing_evidence"]
