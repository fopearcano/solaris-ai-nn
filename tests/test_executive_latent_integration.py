"""Tests for the executive across latent (sleep/dream/replay) modes."""

from __future__ import annotations

from solaris_ai_nn.executive.action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    ExecutableScope,
)
from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.executive.inhibition import InhibitionController
from solaris_ai_nn.executive.policy import ExecutiveMode, ExecutivePolicy
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def _embodied(label="explore_safely"):
    return ActionCandidate(
        action_type=ActionCandidateType.SIMULATED_EMBODIED_ACTION,
        label=label, executable_scope=ExecutableScope.SIMULATION_ONLY,
        utility_estimate=0.6, confidence=0.6)


def test_dream_mode_inhibits_external_candidates():
    controller = InhibitionController()
    for mode in ("sleep", "dream", "replay", "consolidation"):
        result = controller.evaluate_action(_embodied(),
                                            {"latent_mode": mode})
        assert result.inhibited, mode
        assert result.family == "context"
        assert mode in result.reason


def test_latent_only_mode_keeps_internal_options():
    policy = ExecutivePolicy()
    mode = policy.determine_mode({"latent_mode": "dream"})
    assert mode == ExecutiveMode.LATENT_ONLY
    assert not policy.allows(
        ActionCandidateType.SIMULATED_EMBODIED_ACTION)
    assert policy.allows(ActionCandidateType.INTERNAL_MAINTENANCE_ACTION)


def test_decide_during_dream_selects_internal_or_no_action():
    layer = ExecutiveLayer()
    desires = [DesireCandidate(proposal="explore_safely", motivation=0.8,
                               confidence=0.7),
               DesireCandidate(proposal="consolidate_memory",
                               motivation=0.5, confidence=0.6)]
    result = layer.decide(desires, context={"latent_mode": "dream"},
                          step=1)
    assert result.selected.action_type \
        != ActionCandidateType.SIMULATED_EMBODIED_ACTION
    assert result.selected.action_type \
        != ActionCandidateType.SIDECAR_SUGGESTION


def test_mysterium_pressure_feeds_novelty_component():
    layer = ExecutiveLayer()
    desires = [DesireCandidate(proposal="explore_safely", motivation=0.5,
                               confidence=0.5)]
    result = layer.decide(desires, context={"mysterium_pressure": 0.9},
                          step=1)
    scored = {s.candidate.label: s for s in result.scores}
    assert scored["explore_safely"].components["novelty_pressure"] > 0.0


def test_latent_budget_inhibits_more_replay():
    controller = InhibitionController()
    desire = DesireCandidate(proposal="run_replay", motivation=0.7,
                             confidence=0.6)
    result = controller.evaluate_desire(
        desire, {"latent_budget_exceeded": True})
    assert result.inhibited
    assert result.family == "resource"


def test_runner_executive_coexists_with_latent(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
    from solaris_ai_nn.signals import canonical as C

    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=lambda step: (
            C.Stimulus(payload=f"p{step % 2}", intensity=0.5)
            if step <= 50 else None),
        enable_latent=True, latent_interval_steps=40,
        enable_executive=True, executive_report_interval_steps=40)
    runner.run()
    assert runner.executive.decisions > 0
    # Each recorded decision carried the latent mode it ran under.
    for row in runner.executive.recorder.rows():
        assert "latent_mode" in row.get("context_summary", {})
