"""Tests for the world model inside the sensorimotor runner."""

from __future__ import annotations

from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)
from solaris_ai_nn.world_model.edges import EdgeType
from solaris_ai_nn.world_model.nodes import NodeType


def _runner(tmp_path, steps=100, **kw):
    runner = SensorimotorSimulationRunner(
        max_steps=steps, seed=5, state_dir=str(tmp_path / "s"),
        enable_world_model=True, **kw)
    runner.run()
    return runner


def test_world_model_disabled_by_default(tmp_path):
    runner = SensorimotorSimulationRunner(max_steps=30, seed=3,
                                          state_dir=str(tmp_path / "s"))
    runner.run()
    assert runner.world_model is None


def test_gridworld_observations_create_nodes(tmp_path):
    runner = _runner(tmp_path)
    graph = runner.world_model.graph
    objects = {n.label for n in graph.find(node_type=NodeType.OBJECT)}
    # The world's object kinds were observed (obstacles always exist).
    assert "obstacle" in objects or "wall" in objects
    assert graph.find(node_type=NodeType.PLACE)  # the grid itself
    assert graph.find(node_type=NodeType.ACTION)
    assert graph.find(node_type=NodeType.REACTION)
    assert graph.find(node_type=NodeType.BOUNDARY)


def test_blocked_actions_create_blocked_by_edges(tmp_path):
    runner = _runner(tmp_path, steps=150)
    graph = runner.world_model.graph
    blocked = [e for e in graph.edges.values()
               if e.type == EdgeType.BLOCKED_BY]
    if runner.collisions or any(r.blocked_reason
                                for r in runner.action_history):
        assert blocked
        edge = max(blocked, key=lambda e: e.observation_count)
        assert graph.nodes[edge.source_node_id].type == NodeType.ACTION


def test_action_valence_outcomes_recorded(tmp_path):
    runner = _runner(tmp_path, steps=150)
    graph = runner.world_model.graph
    if runner.reaction_valences:
        produces = [e for e in graph.edges.values()
                    if e.type == EdgeType.PRODUCES
                    and graph.nodes[e.target_node_id].type
                    == NodeType.REACTION]
        assert produces


def test_artifacts_saved_and_inner_map_carries_summary(tmp_path):
    runner = _runner(tmp_path)
    assert (tmp_path / "s" / "world_model.json").exists()
    model = runner.observer.update()
    assert model.world_model is not None
    assert model.world_model["graph_node_count"] > 1
