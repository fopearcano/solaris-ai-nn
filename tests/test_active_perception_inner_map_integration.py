"""Integration: active perception state in Inner MAP + state graph."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def _controller(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    ctx = {"step": 0, "mysterium_pressure": 0.6,
           "world_model": {"graph_node_count": 10, "unknown_node_count": 3,
                           "prediction_accuracy": 0.5}}
    decision = ctrl.select(ctx)
    ctrl.execute_if_allowed(decision, ctx)
    return ctrl


def test_inner_map_includes_active_perception(tmp_path):
    ctrl = _controller(tmp_path)
    model = InnerMapObserver(active_perception=ctrl).update()
    assert model.active_perception is not None
    assert model.active_perception["enabled"] is True
    assert model.active_perception["authority"] is False
    assert model.active_perception["sampling_policy_mode"] == "balanced"


def test_inner_map_finds_controller_on_developmental(tmp_path):
    ctrl = _controller(tmp_path)

    class FakeDevelopmental:
        def __init__(self, ap):
            self.active_perception = ap

        def summary(self):
            return {"enabled": True}

    model = InnerMapObserver(
        developmental=FakeDevelopmental(ctrl)).update()
    assert model.active_perception is not None


def test_state_graph_has_active_perception_nodes():
    g = build_default_state_graph()
    for node in ("active_sensing_controller", "sampling_policy",
                 "salience_estimator", "uncertainty_estimator",
                 "curiosity_estimator", "information_gain_estimator",
                 "active_attention_controller", "exploration_memory",
                 "stagnation_detector", "active_perception_safety"):
        assert node in g.nodes


def test_state_graph_active_perception_edges():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("active_sensing_controller", "inner_map") in edges
    assert ("curiosity_estimator", "sampling_policy") in edges
