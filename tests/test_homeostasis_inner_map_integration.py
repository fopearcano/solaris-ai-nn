"""Tests for homeostasis inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_inner_map_includes_dominant_need_and_drive():
    regulator = HomeostaticRegulator()
    regulator.update({"embodiment": {"energy": 0.8, "max_energy": 10.0,
                                     "exhausted": True}})
    model = InnerMapObserver(homeostasis=regulator).update()
    assert model.homeostasis is not None
    assert model.homeostasis["dominant_need"] == "restore_energy"
    assert model.homeostasis["dominant_drive"] == "energy_drive"
    for key in ("current_valence", "valence_trend", "being_pressure",
                "not_being_pressure", "auto_determination_tension",
                "conflict_count", "suppressed_desire_count",
                "last_desire_candidates"):
        assert key in model.homeostasis, key
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.homeostasis["dominant_need"] == "restore_energy"


def test_homeostasis_absent_when_disabled():
    assert InnerMapObserver().update().homeostasis is None


def test_observer_picks_homeostasis_from_runner(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3, enable_homeostasis=True,
                              homeostasis_update_interval_steps=10)
    runner.run()
    model = runner.observer.update()
    assert model.homeostasis is not None  # via runner duck-typing


def test_state_graph_includes_homeostasis_nodes():
    graph = build_default_state_graph()
    for node in ("homeostatic_regulator", "homeostatic_state",
                 "need_estimator", "drive_resolver", "valence_estimator",
                 "auto_determination_engine", "conflict_resolver",
                 "desire_synthesis_engine", "need_memory"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("telemetry", "homeostatic_state") in edges
    assert ("homeostatic_state", "need_estimator") in edges
    assert ("need_estimator", "drive_resolver") in edges
    assert ("drive_resolver", "desire_synthesis_engine") in edges
    assert ("conflict_resolver", "desire_synthesis_engine") in edges
    assert ("desire_synthesis_engine", "bridge") in edges
    assert ("homeostatic_regulator", "inner_map") in edges
    assert "need_estimator" in graph.to_mermaid()
