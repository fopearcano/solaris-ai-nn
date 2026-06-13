"""Integration: hypothesis state in Inner MAP + state graph."""

from __future__ import annotations

from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def _engine(tmp_path):
    engine = HypothesisEngine(state_dir=tmp_path)
    engine.tick({"mysterium_pressure": 0.7,
                 "world_model": {"weak_edges": ["a|predicts|b"]},
                 "after": {"mysterium_pressure": 0.5}})
    return engine


def test_inner_map_includes_hypothesis(tmp_path):
    model = InnerMapObserver(hypothesis=_engine(tmp_path)).update()
    assert model.hypothesis is not None
    assert model.hypothesis["enabled"] is True
    assert model.hypothesis["authority"] is False
    assert "hypothesis_count" in model.hypothesis


def test_inner_map_finds_engine_on_developmental(tmp_path):
    engine = _engine(tmp_path)

    class FakeDevelopmental:
        def __init__(self, e):
            self.hypothesis_engine = e

        def summary(self):
            return {"enabled": True}

    model = InnerMapObserver(
        developmental=FakeDevelopmental(engine)).update()
    assert model.hypothesis is not None


def test_state_graph_has_hypothesis_nodes():
    g = build_default_state_graph()
    for node in ("hypothesis_source_scanner", "hypothesis_generator",
                 "experiment_design", "intervention_plan",
                 "hypothesis_test_runner", "evidence_ledger",
                 "falsification_engine", "hypothesis_memory",
                 "hypothesis_prioritizer", "hypothesis_safety"):
        assert node in g.nodes


def test_state_graph_hypothesis_edges():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("hypothesis_memory", "inner_map") in edges
    assert ("hypothesis_test_runner", "evidence_ledger") in edges
