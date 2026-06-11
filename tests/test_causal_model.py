"""Tests for the CausalAssociationModel."""

from __future__ import annotations

from solaris_ai_nn.world_model.causal_model import CausalAssociationModel
from solaris_ai_nn.world_model.graph import KnowledgeGraph


def test_candidate_causal_edge_scored():
    model = CausalAssociationModel()
    for _ in range(5):
        model.observe_chain([{"label": "signal:light"},
                             {"label": "action:approach",
                              "intervention": True},
                             {"label": "reaction", "valence": 1.0}])
    score = model.score_candidate("action:approach", "reaction")
    assert score["score"] > 0
    assert score["label"] == "causes_candidate"  # structurally hedged
    top = model.top_candidates(2)
    assert top[0]["score"] >= top[1]["score"]


def test_confidence_and_evidence_count_exposed():
    model = CausalAssociationModel()
    model.observe_chain([{"label": "a"}, {"label": "b"}])
    score = model.score_candidate("a", "b")
    assert 0 < score["confidence"] < 0.95
    assert score["evidence_count"] == 1
    assert score["evidence"]["precedence"] == 1
    # No evidence at all: honest zero.
    empty = model.score_candidate("x", "y")
    assert empty["score"] == 0.0 and empty["confidence"] == 0.0


def test_intervention_outweighs_precedence():
    model = CausalAssociationModel()
    model.observe_chain([{"label": "a"}, {"label": "b"}])
    model.observe_chain([{"label": "c", "intervention": True},
                         {"label": "d"}])
    assert model.score_candidate("c", "d")["score"] \
        > model.score_candidate("a", "b")["score"]


def test_counterfactual_evidence_marked_simulated():
    model = CausalAssociationModel()
    model.observe_chain([{"label": "a", "simulated": True}, {"label": "b"}])
    model.observe_counterfactual_divergence("a", "b", divergence=0.6)
    score = model.score_candidate("a", "b")
    assert score["simulated_evidence"] == 2
    assert score["evidence"]["counterfactual"] == 2
    explanation = model.explain_candidate("a", "b")
    assert "offline simulated replay" in explanation
    assert "not proven causation" in explanation


def test_update_graph_creates_hedged_edges():
    model = CausalAssociationModel()
    for _ in range(3):
        model.observe_chain([{"label": "light"},
                             {"label": "warmth", "valence": 0.5}])
    graph = KnowledgeGraph()
    touched = model.update_graph(graph)
    assert touched == 1
    edge = list(graph.edges.values())[0]
    assert edge.type == "causes_candidate"
    assert edge.confidence < 0.95


def test_explain_unknown_pair():
    model = CausalAssociationModel()
    text = model.explain_candidate("never", "seen")
    assert "does not know" in text


def test_to_dict_hedges():
    model = CausalAssociationModel()
    data = model.to_dict()
    assert "nothing is proven" in data["note"]
