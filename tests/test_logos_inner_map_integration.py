"""Integration: LOGOS state in Inner MAP + state graph."""

from __future__ import annotations

from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.logos_complexity import LogosComplexityEngine


def _engine(tmp_path):
    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"world_model": {"contradiction_edges": ["a|c|b"]},
                 "mysterium_pressure": 0.6, "state_dir": str(tmp_path)})
    return engine


def test_inner_map_includes_logos(tmp_path):
    model = InnerMapObserver(logos=_engine(tmp_path)).update()
    assert model.logos is not None
    assert model.logos["enabled"] is True
    assert model.logos["authority"] is False
    assert "complexity_band" in model.logos


def test_inner_map_finds_engine_on_developmental(tmp_path):
    engine = _engine(tmp_path)

    class FakeDevelopmental:
        def __init__(self, e):
            self.logos = e

        def summary(self):
            return {"enabled": True}

    model = InnerMapObserver(
        developmental=FakeDevelopmental(engine)).update()
    assert model.logos is not None


def test_state_graph_has_logos_nodes():
    g = build_default_state_graph()
    for node in ("fracture_detector", "logos_tension", "synthesis_engine",
                 "complexity_regulator", "resolution_policy",
                 "opposition_memory", "esc_process", "dialectical_trace",
                 "logos_complexity_safety"):
        assert node in g.nodes


def test_state_graph_logos_edges():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("opposition_memory", "inner_map") in edges
    assert ("logos_tension", "synthesis_engine") in edges
