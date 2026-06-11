"""Tests for the AssociationLearner."""

from __future__ import annotations

from solaris_ai_nn.world_model.associations import AssociationLearner
from solaris_ai_nn.world_model.graph import KnowledgeGraph


def test_repeated_observations_strengthen_association():
    learner = AssociationLearner()
    for _ in range(10):
        learner.observe({"pattern": "light", "action": "approach"})
    learner.observe({"pattern": "noise", "action": "withdraw"})
    strongest = learner.strongest_associations(1)[0]
    assert strongest["source"] == "light"
    assert strongest["target"] == "approach"
    assert strongest["count"] == 10
    assert strongest["weight"] > 9
    assert strongest["confidence"] > 0.8


def test_all_association_kinds_observed():
    learner = AssociationLearner()
    learner.observe({"pattern": "light", "action": "approach"})
    learner.observe({"action": "approach", "valence": 0.9})
    learner.observe({"context": "awake", "signal": "Stimulus"})
    learner.observe({"entity": "lab_mic", "outcome": "sound"})
    learner.observe({"is_absence": True, "action": "observe"})
    learner.observe({"logos_fracture": 0.8, "tendency": "exploration"})
    learner.observe({"energy_low": True})
    learner.observe({"action": "move_north", "blocked_reason": "wall"})
    kinds = {a.kind for a in learner.associations.values()}
    assert kinds == {"pattern_action", "action_valence", "context_signal",
                     "entity_outcome", "absence_action",
                     "fracture_tendency", "energy_rest", "boundary_blocked"}


def test_entropy_computed():
    learner = AssociationLearner()
    assert learner.association_entropy() == 0.0
    for _ in range(8):
        learner.observe({"pattern": "light", "action": "approach"})
    # One dominant association: near-zero entropy.
    single = learner.association_entropy()
    learner.observe({"pattern": "noise", "action": "withdraw"})
    learner.observe({"pattern": "food", "action": "consume"})
    spread = learner.association_entropy()
    assert spread > single


def test_update_graph_writes_weights():
    learner = AssociationLearner()
    for _ in range(5):
        learner.observe({"pattern": "light", "action": "approach"})
    graph = KnowledgeGraph()
    touched = learner.update_graph(graph)
    assert touched == 1
    edge = list(graph.edges.values())[0]
    assert edge.weight == 5.0
    assert edge.observation_count == 5
    # Re-writing is idempotent on weights (set, not accumulated).
    learner.update_graph(graph)
    assert list(graph.edges.values())[0].weight == 5.0


def test_decay_and_to_dict():
    learner = AssociationLearner(decay_factor=0.5)
    learner.observe({"pattern": "light", "action": "approach"})
    learner.decay()
    assert learner.strongest_associations(1)[0]["weight"] == 0.5
    data = learner.to_dict()
    assert data["association_count"] == 1
    assert data["observed_total"] == 1
    assert "entropy_bits" in data
