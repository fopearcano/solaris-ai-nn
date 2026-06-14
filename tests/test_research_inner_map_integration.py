"""Research <-> Inner MAP: model field + state-graph nodes."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_model_has_research_field():
    assert InnerMapModel().research_lab is None


def test_observer_populates_research():
    observer = InnerMapObserver(research_lab={
        "research_lab_enabled": True, "current_experiment": "EXP_1",
        "harmful_module_candidates": ["enable_world_model"],
        "inconclusive_module_candidates": []})
    model = observer.update()
    assert model.research_lab is not None
    assert model.research_lab["current_experiment"] == "EXP_1"
    assert model.research_lab["harmful_module_candidates"] == [
        "enable_world_model"]


def test_state_graph_has_research_nodes():
    g = build_default_state_graph()
    for node in ("ExperimentDesign", "BaselineAgent", "SolarisVariantConfig",
                 "AblationMatrix", "ResearchBenchmarkRunner",
                 "ResearchResultStore", "ResearchMetricsSuite", "NullModel",
                 "ComparisonEngine", "EffectAnalyzer",
                 "ResearchReproducibilityBuilder", "ResearchLeaderboard",
                 "ResearchReportBuilder"):
        assert node in g.nodes


def test_state_graph_research_edges():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("ExperimentDesign", "ResearchBenchmarkRunner") in pairs
    assert ("ResearchResultStore", "ComparisonEngine") in pairs
    assert ("ComparisonEngine", "EffectAnalyzer") in pairs
