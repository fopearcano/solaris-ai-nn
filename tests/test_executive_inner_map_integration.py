"""Tests for the executive inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def _layer():
    layer = ExecutiveLayer()
    layer.decide([DesireCandidate(proposal="rest", motivation=0.6,
                                  confidence=0.6)], context={}, step=1)
    return layer


def test_inner_map_includes_executive_summary():
    model = InnerMapObserver(executive=_layer()).update()
    assert model.executive is not None
    for key in ("mode", "active_focus", "desire_queue_length",
                "selected_action_suggestion", "inhibited_candidate_count",
                "no_safe_action_count", "last_arbitration_score",
                "decisions"):
        assert key in model.executive, key
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.executive["mode"] == "arbitrated"


def test_executive_absent_when_disabled():
    assert InnerMapObserver().update().executive is None


def test_observer_picks_executive_from_runner(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=60,
                              seed=3, enable_executive=True,
                              executive_report_interval_steps=20)
    runner.run()
    model = runner.observer.update()
    assert model.executive is not None  # via runner duck-typing
    assert model.executive["enabled"] is True


def test_state_graph_includes_executive_nodes():
    graph = build_default_state_graph()
    for node in ("desire_queue", "inhibition_controller",
                 "action_arbitrator", "prospection_engine",
                 "short_horizon_planner", "executive_working_memory",
                 "attention_selector", "decision_trace_recorder",
                 "executive_policy", "executive_safety_validator"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("desire_synthesis_engine", "desire_queue") in edges
    assert ("world_model_predictor", "prospection_engine") in edges
    assert ("inhibition_controller", "action_arbitrator") in edges
    assert ("action_arbitrator", "bridge") in edges
    assert ("executive_policy", "inner_map") in edges
    assert "action_arbitrator" in graph.to_mermaid()
