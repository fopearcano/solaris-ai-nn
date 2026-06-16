"""Post-merge runtime: bounded, registry updated, no Git/GitHub/source/validation."""

from __future__ import annotations

import inspect

from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime
from solaris_ai_nn.post_merge_assimilation import post_merge_runtime


def _bundle():
    return {
        "merge_manifest": {"merge_id": "m1",
                           "confirmation": {"confirmed_by_operator": True}},
        "implementation_intake": {"merge_recommendation_status":
                                  "recommend_merge",
                                  "critical_safety_regression_count": 0,
                                  "spec_compliance_status": "satisfied",
                                  "test_failure_count": 0},
        "validation_results": {"full_test_run": {"passed": True},
                               "safety_invariant_run": {"passed": True},
                               "claimguard_run": {"safe": True},
                               "mini_soak": {"passed": True}},
        "parent_metrics": {"sensorium_metrics": 0.5},
        "candidate_metrics": {"sensorium_metrics": 0.6}}


def test_bounded_runtime(tmp_path):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    rt.load_bundle(_bundle())
    out = rt.run()
    assert out["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    rt.load_bundle(_bundle())
    assert rt.run()["refused"] is True


def test_baseline_registry_updated(tmp_path):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    rt.load_bundle(_bundle())
    rt.run()
    assert rt.registry.get("b1") is not None
    assert rt.registry.status()["baseline_record_count"] == 2


def test_reports_generated(tmp_path):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    rt.load_bundle(_bundle())
    rt.run()
    out = rt.write_artifacts()
    import os
    assert os.path.isfile(out["markdown"])
    assert len(out["documents"]) >= 8


def test_status_disclaims_actions(tmp_path):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_bundle())
    rt.run()
    st = rt.post_merge_status()
    assert st["modifies_source"] is False
    assert st["runs_git"] is False
    assert st["calls_github"] is False
    assert st["merges_pr"] is False
    assert st["runs_validation"] is False


def test_no_git_github_source_validation_in_source():
    src = inspect.getsource(post_merge_runtime)
    assert "subprocess" not in src
    assert "gh pr" not in src
    assert "git checkout" not in src
    assert "github api" not in src.lower()
