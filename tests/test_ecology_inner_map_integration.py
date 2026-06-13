"""Integration: ecology state surfaces in the Inner MAP + state graph."""

from __future__ import annotations

from solaris_ai_nn.ecology.nursery import DevelopmentalNursery, NurseryConfig
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def _nursery(tmp_path):
    nursery = DevelopmentalNursery(config=NurseryConfig(
        seed=7, duration_steps=80, output_state_dir=str(tmp_path)))
    for step in range(80):
        nursery.stimulus_provider(step)
    return nursery


def test_observer_pulls_ecology_summary(tmp_path):
    nursery = _nursery(tmp_path)
    observer = InnerMapObserver(ecology=nursery)
    model = observer.update()
    assert model.ecology is not None
    assert model.ecology["enabled"] is True
    assert model.ecology["authority"] is False


def test_observer_finds_nursery_on_developmental(tmp_path):
    # The observer resolves the nursery from a developmental runtime that
    # exposes a ``.nursery`` attribute, even when ``ecology=`` is omitted.
    nursery = _nursery(tmp_path)

    class FakeDevelopmental:
        def __init__(self, nursery):
            self.nursery = nursery

        def summary(self):
            return {"enabled": True}

    observer = InnerMapObserver(developmental=FakeDevelopmental(nursery))
    model = observer.update()
    assert model.ecology is not None
    assert model.ecology["enabled"] is True


def test_state_graph_has_ecology_nodes():
    graph = build_default_state_graph()
    for node in ("developmental_nursery", "stimulus_ecology",
                 "cycle_manager", "regime_manager", "scarcity_model",
                 "novelty_generator", "anomaly_generator",
                 "seasonality_model", "deprivation_model",
                 "delayed_consequence_model", "ecology_stream",
                 "ecology_memory"):
        assert node in graph.nodes


def test_state_graph_ecology_feeds_inner_map():
    graph = build_default_state_graph()
    edges = {(s, d) for s, d, _ in graph.edges}
    assert ("developmental_nursery", "inner_map") in edges
    assert ("ecology_stream", "bridge") in edges
