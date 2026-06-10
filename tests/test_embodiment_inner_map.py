"""Tests for embodiment in the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.embodiment.simulation_runner import SensorimotorSimulationRunner
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

EMBODIMENT_NODES = {"simulated_body", "grid_world", "sensors", "effectors",
                    "energy_model", "embodiment_safety", "sensorimotor_runner"}


def test_inner_map_includes_body_and_world_state():
    runner = SensorimotorSimulationRunner(max_steps=40, seed=5)
    runner.run()
    model = runner.observer.update()
    emb = model.embodiment
    assert emb is not None
    assert emb["body"] is True
    assert emb["body_type"] == "SimulatedBody"
    assert emb["environment_type"] == "GridWorld"
    assert isinstance(emb["position"], list)
    assert "energy" in emb and "exhausted" in emb
    assert emb["action_authority"] == "simulation-only"
    assert "leave_simulation" in emb["forbidden_actions"]
    assert "environment_boundaries" in emb


def test_inner_map_serializes_with_embodiment():
    runner = SensorimotorSimulationRunner(max_steps=20, seed=5)
    runner.run()
    d = runner.observer.update().to_dict()
    assert "embodiment" in d
    assert d["embodiment"]["action_authority"] == "simulation-only"


def test_state_graph_includes_embodiment_nodes():
    g = build_default_state_graph()
    assert EMBODIMENT_NODES <= set(g.nodes)
    labels = {(s, d): l for s, d, l in g.edges}
    assert labels.get(("grid_world", "sensors")) == "produces sensory data"
    assert ("sensors", "bridge") in labels
    assert ("embodiment_safety", "effectors") in labels
    # Renders without error.
    assert "simulated_body" in g.to_mermaid()
    assert "grid_world" in g.to_dot()
