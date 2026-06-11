"""Tests for world-model evidence feeding executive prospection."""

from __future__ import annotations

from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
)
from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.executive.prospection import ProspectionEngine
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def _candidate(label="approach_reward"):
    return ActionCandidate(
        action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
        label=label, executable_scope=ExecutableScope.SIMULATION_ONLY,
        utility_estimate=0.5, confidence=0.5)


def test_world_model_valence_grounds_prospection():
    engine = ProspectionEngine()
    evidenced = engine.simulate_candidate(_candidate(), {
        "world_model_valence": {"approach_reward": 0.7},
        "anticipation_accuracy": 0.8})
    assert evidenced.outcome == "favorable"
    assert evidenced.expected_valence == 0.7
    assert any("world model" in b for b in evidenced.basis)
    assert evidenced.simulated is True


def test_no_world_model_evidence_yields_unknown():
    engine = ProspectionEngine()
    blind = engine.simulate_candidate(_candidate("look"), {})
    assert blind.outcome == "unknown"
    assert blind.confidence <= 0.2
    assert any("not invented" in b for b in blind.basis)
    assert engine.unknown_total == 1


def test_world_model_support_shifts_arbitration():
    layer = ExecutiveLayer()
    desires = [DesireCandidate(proposal="look", motivation=0.5,
                               confidence=0.5),
               DesireCandidate(proposal="rest", motivation=0.5,
                               confidence=0.5)]
    result = layer.decide(desires, context={
        "world_model_support": {"look": 1.0},
        "world_model_valence": {"look": 0.6}}, step=1)
    scored = {s.candidate.label: s for s in result.scores}
    assert scored["look"].components["world_model_support"] > 0.0
    assert scored["look"].components["world_model_support"] \
        > scored["rest"].components["world_model_support"]


def test_negative_world_model_valence_counts_against():
    engine = ProspectionEngine()
    result = engine.simulate_candidate(_candidate("seek_signal"), {
        "world_model_valence": {"seek_signal": -0.6}})
    assert result.outcome == "unfavorable"


def test_runner_passes_world_model_context(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
    from solaris_ai_nn.signals import canonical as C

    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=lambda step: (
            C.Stimulus(payload=f"p{step % 2}", intensity=0.5)
            if step <= 80 else None),
        enable_world_model=True, enable_executive=True,
        executive_report_interval_steps=40)
    runner.run()
    assert runner.executive.decisions > 0
    assert runner.world_model is not None
    # The real world model graph was never mutated by prospection.
    assert runner.world_model.world_model_summary()["graph_node_count"] >= 1
