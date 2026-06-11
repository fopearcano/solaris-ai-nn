"""Tests for the prospection engine."""

from __future__ import annotations

from solaris_ai_nn.embodiment.grid_world import GridWorld
from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
)
from solaris_ai_nn.executive.prospection import (
    MAX_HORIZON,
    ProspectionEngine,
)


def _candidate(label):
    return ActionCandidate(
        action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
        label=label, executable_scope=ExecutableScope.SIMULATION_ONLY)


def test_candidate_simulation_bounded():
    engine = ProspectionEngine()
    result = engine.simulate_candidate(_candidate("rest"), {
        "world_model_valence": {"rest": 0.4}}, horizon=99)
    assert result.horizon <= MAX_HORIZON
    assert result.simulated is True
    sequence = engine.simulate_sequence([_candidate("look")] * 10, {},
                                        horizon=99)
    assert sequence.horizon <= 5  # the hard cap on chained estimates


def test_insufficient_data_returns_unknown():
    engine = ProspectionEngine()
    result = engine.simulate_candidate(_candidate("look"), {})
    assert result.outcome == "unknown"
    assert result.confidence <= 0.1
    assert "not invented" in result.basis[0]
    assert engine.unknown_total == 1


def test_evidence_yields_estimate_with_confidence():
    engine = ProspectionEngine()
    result = engine.simulate_candidate(_candidate("approach_reward"), {
        "world_model_valence": {"approach_reward": 0.6},
        "habit_weights": {"approach_reward": 0.5},
        "anticipation_accuracy": 0.8})
    assert result.outcome == "favorable"
    assert result.expected_valence is not None
    assert 0 < result.confidence < 0.9
    assert len(result.basis) >= 3


def test_gridworld_sandbox_does_not_mutate_real_state():
    world = GridWorld(seed=5)
    objects_before = dict(world.objects)
    agent_before = world.agent_pos
    engine = ProspectionEngine()
    for label in ("approach_reward", "explore_safely", "rest"):
        engine.simulate_candidate(_candidate(label), {
            "grid_world": world, "position": world.agent_pos})
    assert world.objects == objects_before
    assert world.agent_pos == agent_before


def test_sandbox_risk_scales_with_danger():
    world = GridWorld(seed=5)
    engine = ProspectionEngine()
    moving = engine.simulate_candidate(_candidate("approach_reward"), {
        "grid_world": world, "habit_weights": {"approach_reward": 0.2}})
    resting = engine.simulate_candidate(_candidate("rest"), {
        "grid_world": world, "habit_weights": {"rest": 0.2}})
    assert moving.expected_risk >= resting.expected_risk


def test_sequence_confidence_decays():
    engine = ProspectionEngine()
    context = {"world_model_valence": {"look": 0.3, "rest": 0.3},
               "anticipation_accuracy": 0.8}
    one = engine.simulate_sequence([_candidate("look")], context)
    three = engine.simulate_sequence(
        [_candidate("look"), _candidate("rest"), _candidate("look")],
        context)
    assert three.confidence < one.confidence
    assert three.horizon == 3
    assert all(s.simulated for s in three.scenarios)


def test_compare_candidates_feeds_arbitration():
    engine = ProspectionEngine()
    out = engine.compare_candidates(
        [_candidate("rest"), _candidate("look")],
        {"world_model_valence": {"rest": 0.5}})
    assert out["rest"]["expected_valence"] == 0.5
    assert out["look"]["outcome"] == "unknown"
    assert "never facts" in engine.snapshot()["note"]
