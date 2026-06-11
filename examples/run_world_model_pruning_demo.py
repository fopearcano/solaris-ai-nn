#!/usr/bin/env python3
"""World model pruning demo: synthesis through subtraction, dry-run only.

    python examples/run_world_model_pruning_demo.py --dry-run

Builds a graph with both strong (often-observed) and weak (one-off)
structure, proposes pruning, and applies it in dry-run mode: the subtraction
report is printed, evidence summaries are preserved, and the graph is
provably unchanged. Production pruning requires governance approval and an
explicit flag -- this demo never deletes anything.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.world_model import (
    EdgeType,
    KnowledgeGraph,
    NodeType,
    WorldModelQueryInterface,
    GraphSynthesisPruner,
    WorldModelBuilder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="World model pruning demo")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="always on: this demo never deletes")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/world_pruning")
    args = parser.parse_args()

    builder = WorldModelBuilder()
    graph = builder.graph

    # Strong structure: observed many times.
    light = graph.upsert_node(NodeType.STIMULUS_PATTERN, "light", "demo")
    approach = graph.upsert_node(NodeType.ACTION, "approach", "demo")
    for i in range(12):
        graph.upsert_edge(light, EdgeType.PRODUCES, approach,
                          evidence={"step": i})
    # Weak structure: seen once, never again.
    for i in range(6):
        stray = graph.upsert_node(NodeType.STIMULUS_PATTERN,
                                  f"one_off_{i}", "demo")
        target = graph.upsert_node(NodeType.STATE, f"transient_{i}", "demo")
        graph.upsert_edge(stray, EdgeType.CO_OCCURS_WITH, target,
                          weight_delta=0.1)
    # A redundant unknown duplicate of a typed node.
    graph.upsert_node(NodeType.UNKNOWN, "light", "demo")

    nodes_before = len(graph.nodes)
    edges_before = len(graph.edges)
    pruner = builder.pruner
    proposal = pruner.propose_pruning(graph, threshold=0.5)
    report = pruner.apply_pruning(graph, proposal, dry_run=True)

    print("=" * 70)
    print("Solaris-AI-NN -- world model pruning demo (dry-run only)")
    print("=" * 70)
    print(f"graph before:     {nodes_before} nodes, {edges_before} edges")
    print(f"proposal:         {proposal['totals']['edges']} weak edge(s), "
          f"{proposal['totals']['nodes']} weak node(s), "
          f"{proposal['totals']['merges']} redundant merge(s)")
    print(f"dry run:          {report['dry_run']}")
    print(f"would remove:     {report['would_remove']}")
    print(f"graph after:      {len(graph.nodes)} nodes, "
          f"{len(graph.edges)} edges (unchanged: "
          f"{len(graph.nodes) == nodes_before and len(graph.edges) == edges_before})")
    print(f"evidence kept:    {report['evidence_preserved']} "
          f"({len(proposal['evidence_summary']['edges'])} edge summaries)")
    print(f"reversible:       {report['reversible']}")
    print()
    queries = WorldModelQueryInterface(builder=builder)
    answer = queries.answer("what was pruned from the graph?")
    print(f"Q: what was pruned from the graph?")
    print(f"A: {answer.text}")
    print()
    print("note: production pruning requires governance approval "
          "(enable_world_model_pruning); this demo is structurally dry-run.")


if __name__ == "__main__":
    main()
