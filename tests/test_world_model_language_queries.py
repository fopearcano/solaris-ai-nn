"""Tests for the world-model language queries."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.world_model.builder import WorldModelBuilder
from solaris_ai_nn.world_model.query import WorldModelQueryInterface


def _fed_builder():
    builder = WorldModelBuilder()
    for _ in range(6):
        builder.update_from_reaction("approach", 1.0)
    builder.update_from_latent_report({
        "mysterium_reasons": ["repeated prediction misses"],
        "mode": "replay"})
    return builder


def test_world_model_know_query_grounded():
    queries = WorldModelQueryInterface(builder=_fed_builder())
    result = queries.answer("What does the world model know?")
    assert result.answered
    assert "nodes" in result.text and "relations" in result.text
    assert "observed associations" in result.text
    assert "not human-like understanding" in result.text


def test_strongest_association_query():
    queries = WorldModelQueryInterface(builder=_fed_builder())
    result = queries.answer("what is the strongest association")
    assert result.answered
    assert "approach" in result.text
    assert "observed association" in result.text.lower() \
        or "strongest observed" in result.text.lower()


def test_prediction_query_hedged():
    queries = WorldModelQueryInterface(builder=_fed_builder())
    result = queries.answer("what does the graph predict next?")
    assert "graph counts" in result.text or "insufficient" in result.text
    assert "never" in result.text or "insufficient" in result.text


def test_unknowns_reported_safely():
    queries = WorldModelQueryInterface(builder=_fed_builder())
    result = queries.answer("what is still unknown?")
    assert result.answered
    assert "unknown" in result.text.lower()
    # On an empty model the answer stays honest, not falsely confident.
    empty = WorldModelQueryInterface(builder=WorldModelBuilder())
    result = empty.answer("what is still unknown?")
    assert "not that everything is known" in result.text


def test_pruning_and_gridworld_queries():
    builder = _fed_builder()
    queries = WorldModelQueryInterface(builder=builder)
    assert "No graph pruning" in queries.answer(
        "what was pruned from the graph?").text
    proposal = builder.pruner.propose_pruning(builder.graph)
    builder.pruner.apply_pruning(builder.graph, proposal, dry_run=True)
    assert "dry-run" in queries.answer(
        "what was pruned from the graph?").text
    assert "no GridWorld observations" in queries.answer(
        "what did the system learn in gridworld?").text


def test_unknown_query_falls_back_honestly():
    queries = WorldModelQueryInterface(builder=_fed_builder())
    result = queries.answer("does the graph love me?")
    assert not result.answered
    assert "does not know how to answer" in result.text


def test_all_answers_claim_safe():
    queries = WorldModelQueryInterface(builder=_fed_builder())
    guard = ClaimGuard()
    for question in queries.supported_queries():
        answer = queries.answer(question)
        assert guard.is_safe(answer.text), question
