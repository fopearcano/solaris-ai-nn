#!/usr/bin/env python3
"""Pilot-3 action grounding demo: action-grounded symbol + edge, graded.

    python examples/run_pilot3_action_grounding_demo.py --state-dir .solaris_ai_nn_pilot3/test_action_grounding

Shows an action-grounded proto-symbol (marked simulation-scoped), a simulated
action world-model edge (marked simulation-scoped), and the action-grounding
quality classification. Action grounding is operational and simulation-scoped:
it is not real embodiment, not free will, and not real-world competence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.protolanguage.symbol_registry import (
    PILOT3_SYMBOL_CATEGORIES,
    SymbolRegistry,
)
from solaris_ai_nn.world_model.graph import (
    PILOT3_ACTION_EDGE_KINDS,
    KnowledgeGraph,
)
from solaris_ai_nn.pilot3 import ActionGroundingAnalyzer, ActionGroundingQuality


def main():
    parser = argparse.ArgumentParser(
        description="Pilot-3 action grounding demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/test_action_grounding")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    # An action-grounded proto-symbol, marked simulation-scoped.
    registry = SymbolRegistry(state_dir=args.state_dir)
    symbol = registry.upsert_symbol(
        symbol_type="action_symbol",
        grounding_summary="move_east->wall_reaction",
        evidence_refs=["sim_step_1", "sim_step_2"],
        source_module="motor_membrane", evidence_kind="simulated",
        metadata={"pilot3_category": "action_reaction_loop_symbol",
                  "simulation_scoped": True})

    # A simulated action world-model edge, marked simulation-scoped via the
    # pilot3_kind metadata tag (the edge type stays a normal EdgeType).
    graph = KnowledgeGraph()
    a = graph.upsert_node("action", "move_east")
    b = graph.upsert_node("reaction", "blocked")
    edge = graph.upsert_edge(a, "causes_candidate", b,
                             simulation_scoped=True,
                             pilot3_kind="simulated_action_edge")

    # Grade the action grounding.
    ag = ActionGroundingAnalyzer()
    rec = ag.add("proto_symbol", repeated_action_reaction_loop=True,
                 predicted_consequence_improved=True,
                 symbol_linked_to_action_and_consequence=True,
                 world_model_edge_repeated=True, evidence_refs=["r1", "r2"])

    print("=== Pilot-3 action grounding demo ===")
    print(f"symbol token          : {symbol.token}")
    print(f"symbol category       : {symbol.metadata.get('pilot3_category')} "
          f"(in vocab: {symbol.metadata.get('pilot3_category') in PILOT3_SYMBOL_CATEGORIES})")
    print(f"symbol simulation-scoped: {symbol.metadata.get('simulation_scoped')}")
    print(f"edge pilot3 kind      : {edge.metadata.get('pilot3_kind')} "
          f"(in vocab: {edge.metadata.get('pilot3_kind') in PILOT3_ACTION_EDGE_KINDS})")
    print(f"edge simulation-scoped: {edge.metadata.get('simulation_scoped')}")
    print(f"grounding quality     : {rec.quality} "
          f"(strong/moderate/weak are simulation-scoped)")
    print(f"valid qualities       : {list(ActionGroundingQuality.ALL)}")
    print("note                  : action grounding is operational and "
          "simulation-scoped; not real embodiment")


if __name__ == "__main__":
    main()
