#!/usr/bin/env python3
"""Artifact graph demo: evidence provenance, contradictions stay visible.

    python examples/run_artifact_graph_demo.py

Builds the research artifact graph for a clean cycle and for a cycle with a
critical regression and a falsified claim. The graph records derived_from
provenance between artifacts, surfaces missing artifacts as missing nodes, and
keeps contradictions (falsifies / blocks / safety_blocks) visible -- it never
collapses conflicting evidence into a single score.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_cycle import ArtifactGraphBuilder


def _show(label, bundle):
    graph = ArtifactGraphBuilder().build(bundle).to_dict()
    print(f"=== {label} ===")
    print(f"  nodes: {graph['artifact_graph_node_count']} "
          f"(missing {len(graph['missing_nodes'])}: {graph['missing_nodes']})")
    print(f"  contradictions: {graph['artifact_graph_contradiction_count']}")
    for e in graph["edges"]:
        detail = f" -- {e['detail']}" if e["detail"] else ""
        print(f"    {e['src']} --[{e['edge_type']}]--> {e['dst']}{detail}")


def main():
    argparse.ArgumentParser(description="Artifact graph demo").parse_args()

    _show("Clean cycle (full provenance chain)", {
        "research_baseline": {"baseline_status": "validated"},
        "roadmap": {"roadmap_item_count": 3},
        "architecture_evolution": {"proposal_count": 2},
        "experiment_compiler": {"ready_spec_count": 2},
        "implementation_intake": {"merge_recommendation_status": "recommend"},
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0},
        "operator_decisions": [
            {"decision_type": "confirm_external_merge", "status": "approved"}],
    })
    print()
    _show("Cycle with regression + falsified claim (missing post-merge)", {
        "research_baseline": {"baseline_status": "in_progress"},
        "roadmap": {"roadmap_item_count": 3},
        "architecture_evolution": {"proposal_count": 1},
        "experiment_compiler": {"ready_spec_count": 1},
        "implementation_intake": {
            "merge_recommendation_status": "block_merge_due_to_safety"},
        "falsification": {"falsified_claim_count": 1},
        "contradictions": [{"src": "soak_dossier", "dst": "post_merge_report",
                            "detail": "soak contradicts the post-merge claim"}],
    })
    print()
    print("note: the artifact graph is evidence provenance, not cognition. "
          "Contradictions and missing nodes stay visible; conflicting evidence "
          "is never collapsed into a single score.")


if __name__ == "__main__":
    main()
