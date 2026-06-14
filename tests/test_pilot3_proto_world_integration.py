"""Pilot-3 <-> Proto-language / World model: simulation-scoped markers."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.symbol_registry import (
    PILOT3_SYMBOL_CATEGORIES,
    SymbolRegistry,
)
from solaris_ai_nn.world_model.graph import (
    PILOT3_ACTION_EDGE_KINDS,
    KnowledgeGraph,
)


def test_action_grounded_symbol_marked_simulation_scoped(tmp_path):
    registry = SymbolRegistry(state_dir=str(tmp_path))
    symbol = registry.upsert_symbol(
        symbol_type="action_symbol",
        grounding_summary="move_east->reaction",
        evidence_refs=["sim1", "sim2"], source_module="motor_membrane",
        evidence_kind="simulated",
        metadata={"pilot3_category": "action_grounded_simulated",
                  "simulation_scoped": True})
    assert symbol.metadata["simulation_scoped"] is True
    assert symbol.metadata["pilot3_category"] in PILOT3_SYMBOL_CATEGORIES


def test_symbol_categories_vocabulary():
    assert set(PILOT3_SYMBOL_CATEGORIES) == {
        "action_grounded_simulated", "action_reaction_loop_symbol",
        "blocked_action_symbol", "affordance_symbol", "sandbox_only_symbol"}


def test_simulated_action_edge_marked_simulation_scoped():
    graph = KnowledgeGraph()
    a = graph.upsert_node("action", "move_east")
    b = graph.upsert_node("reaction", "blocked")
    edge = graph.upsert_edge(a, "causes_candidate", b,
                             simulation_scoped=True,
                             pilot3_kind="simulated_action_edge")
    assert edge.metadata["simulation_scoped"] is True
    assert edge.metadata["pilot3_kind"] in PILOT3_ACTION_EDGE_KINDS


def test_blocked_action_edge_kind():
    assert "blocked_action_edge" in PILOT3_ACTION_EDGE_KINDS
    assert "simulated_consequence_edge" in PILOT3_ACTION_EDGE_KINDS
