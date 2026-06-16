"""Research cycle: Inner MAP includes research-cycle tracking state."""

from __future__ import annotations

from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.research_cycle import ResearchCycleRuntime


def _runtime(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "cycle_manifest": {"cycle_id": "cycle_1"},
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0}})
    rt.run()
    return rt


def test_inner_map_includes_research_cycle(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(research_cycle=rt).update()
    assert model.research_cycle is not None
    assert model.research_cycle["research_cycle_enabled"] is True
    assert model.research_cycle["runs_git"] is False
    assert model.research_cycle["calls_github"] is False
    assert model.research_cycle["approves_itself"] is False
    assert "research_cycle" in model.to_dict()


def test_state_graph_has_research_cycle_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "ResearchCycleRuntime" in nodes
    assert "EvidenceContinuityLedger" in nodes
    assert "ResearchCycleDecisionGate" in nodes
