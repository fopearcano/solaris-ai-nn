"""Research baseline runtime: bounded, reports, no Git/GitHub/source/validation."""

from __future__ import annotations

import inspect

from solaris_ai_nn.research_baseline import ResearchBaselineRuntime
from solaris_ai_nn.research_baseline import baseline_runtime


def _bundle(validated=True):
    pm = ({"candidate_baseline_status": "validated",
           "critical_regression_count": 0,
           "rollback_recommendation_status": "no_rollback_needed",
           "unresolved_blockers": []} if validated else
          {"candidate_baseline_status": "blocked_by_safety",
           "critical_regression_count": 2,
           "rollback_recommendation_status": "rollback_recommended",
           "unresolved_blockers": ["x"]})
    return {
        "post_merge": pm,
        "implementation_intake": {"critical_safety_regression_count":
                                  0 if validated else 2},
        "validation_results": {"unit_tests": {"passed": True},
                               "safety_tests": {"passed": validated},
                               "claimguard": {"safe": True},
                               "safety_invariants": {"passed": True}},
        "safety_artifacts": {"passed": validated},
        "snapshot_artifacts": {"evaluation_report": {"payload": {"e": 1}}},
        "available_anchors": {"parent_baseline": "b1"}}


def test_bounded_runtime(tmp_path):
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1")
    rt.load_bundle(_bundle())
    out = rt.run()
    assert out["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is True


def test_reports_generated(tmp_path):
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1")
    rt.load_bundle(_bundle())
    rt.run()
    out = rt.write_artifacts()
    import os
    assert os.path.isfile(out["markdown"])
    assert len(out["documents"]) >= 11


def test_status_disclaims_release(tmp_path):
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1")
    rt.load_bundle(_bundle())
    rt.run()
    st = rt.research_baseline_status()
    assert st["is_git_tag"] is False
    assert st["is_github_release"] is False
    assert st["is_product_release"] is False
    assert st["modifies_source"] is False


def test_no_git_github_source_validation_in_source():
    # No actual Git/GitHub/validation machinery (the words "Git tag" may appear
    # only in the honest "creates no Git tag" disclaimer).
    src = inspect.getsource(baseline_runtime)
    assert "subprocess" not in src
    assert "gh pr" not in src
    assert "git checkout" not in src
    assert "import requests" not in src
    assert "creates no git tag" in src.lower()  # the disclaimer is present
