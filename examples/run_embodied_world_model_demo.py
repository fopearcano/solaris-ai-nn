#!/usr/bin/env python3
"""Embodied world model demo: GridWorld structure enters the graph.

    python examples/run_embodied_world_model_demo.py --steps 300

A bounded sensorimotor session runs with the world model enabled: objects,
obstacles, reward/danger markers, blocked actions, and action->valence
outcomes become inspectable graph structure. Observed structure only -- no
pathfinding, no planning.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)
from solaris_ai_nn.world_model import (
    EdgeType,
    NodeType,
    WorldModelQueryInterface,
    WorldModelReportBuilder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Embodied world model demo")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/embodied_world_model")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    runner = SensorimotorSimulationRunner(
        max_steps=args.steps, seed=args.seed, state_dir=args.state_dir,
        enable_world_model=True)
    runner.run()
    builder = runner.world_model
    graph = builder.graph

    print("=" * 70)
    print("Solaris-AI-NN -- embodied world model demo (GridWorld)")
    print("=" * 70)
    print(f"steps:            {runner.steps_run} "
          f"(rewards {runner.rewards_consumed}, "
          f"collisions {runner.collisions})")
    print(f"graph nodes:      {len(graph.nodes)}")
    print(f"graph edges:      {len(graph.edges)}")
    objects = sorted(n.label for n in graph.find(node_type=NodeType.OBJECT))
    print(f"observed objects: {', '.join(objects)}")
    blocked = graph.strongest_edges(limit=3, edge_type=EdgeType.BLOCKED_BY)
    for edge in blocked:
        print(f"blocked:          {graph.nodes[edge.source_node_id].label!r}"
              f" blocked by {graph.nodes[edge.target_node_id].label!r} "
              f"({edge.observation_count}x)")
    produces = [e for e in graph.strongest_edges(
        limit=10, edge_type=EdgeType.PRODUCES)
        if graph.nodes[e.target_node_id].type == NodeType.REACTION]
    for edge in produces[:3]:
        print(f"outcome:          {graph.nodes[edge.source_node_id].label!r}"
              f" -> {graph.nodes[edge.target_node_id].label!r} "
              f"(weight {edge.weight:.2f})")
    print()
    queries = WorldModelQueryInterface(builder=builder)
    answer = queries.answer("what did the system learn in gridworld?")
    print(f"Q: what did the system learn in gridworld?")
    print(f"A: {answer.text[:200]}")
    print()
    report = WorldModelReportBuilder(builder=builder)
    paths = report.save(f"{args.state_dir}/world_model_report.json",
                        f"{args.state_dir}/world_model_report.md")
    print(f"report: {paths['markdown']} "
          f"(claim guard safe: {paths['claim_guard']['safe']})")


if __name__ == "__main__":
    main()
