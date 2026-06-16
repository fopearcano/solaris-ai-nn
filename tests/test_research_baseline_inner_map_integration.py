"""Research baseline: Inner MAP includes research baseline state."""

from __future__ import annotations

from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.research_baseline import ResearchBaselineRuntime


def _runtime(tmp_path):
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
        "snapshot_artifacts": {"evaluation_report": {"payload": {"e": 1}}}})
    rt.run()
    return rt


def test_inner_map_includes_research_baseline(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(research_baseline=rt).update()
    assert model.research_baseline is not None
    assert model.research_baseline["research_baseline_enabled"] is True
    assert model.research_baseline["is_git_tag"] is False
    assert model.research_baseline["is_github_release"] is False
    assert "research_baseline" in model.to_dict()


def test_state_graph_has_research_baseline_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "ResearchBaselineRuntime" in nodes
    assert "ReproducibilityBundle" in nodes
    assert "BaselineLimitationRegistry" in nodes
