"""Post-merge: Inner MAP includes post-merge assimilation state."""

from __future__ import annotations

from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime


def _runtime(tmp_path):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    rt.load_bundle({
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
        "candidate_metrics": {"sensorium_metrics": 0.6}})
    rt.run()
    return rt


def test_inner_map_includes_post_merge(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(post_merge_assimilation=rt).update()
    assert model.post_merge_assimilation is not None
    assert model.post_merge_assimilation[
        "post_merge_assimilation_enabled"] is True
    assert model.post_merge_assimilation["runs_git"] is False
    assert model.post_merge_assimilation["merges_pr"] is False
    assert "post_merge_assimilation" in model.to_dict()


def test_state_graph_has_post_merge_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "PostMergeAssimilationRuntime" in nodes
    assert "BaselineRegistry" in nodes
    assert "RegressionWatch" in nodes
