"""Tests for homeostasis fed by latent cognition."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.needs import NeedType
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_high_memory_pressure_suggests_consolidation():
    regulator = HomeostaticRegulator()
    result = regulator.update({
        "trace_length": 9500, "trace_capacity": 10000,
        "steps_since_consolidation": 480,
    })
    need = result.need_state.by_type(NeedType.CONSOLIDATE_MEMORY)
    assert need is not None
    proposals = {c.proposal for c in result.desire_candidates
                 if not c.blocked}
    assert "consolidate_memory" in proposals
    assert regulator.drives.state.drives[
        "consolidation_drive"].pressure > 0


def test_high_mysterium_suggests_replay_or_exploration():
    regulator = HomeostaticRegulator()
    result = regulator.update({
        "latent": {"mysterium_pressure": 0.85,
                   "anticipation_accuracy": 0.3},
    })
    need = result.need_state.by_type(NeedType.REDUCE_UNCERTAINTY)
    assert need is not None
    assert "unknown_pressure" in need.source_variables
    proposals = {c.proposal for c in result.desire_candidates
                 if not c.blocked}
    assert proposals & {"run_replay", "explore_safely", "look"}


def test_latent_summary_feeds_variables_in_runner(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
    from solaris_ai_nn.signals import canonical as C

    def provider(step):
        return (C.Stimulus(payload=f"p{step % 2}", intensity=0.5)
                if step <= 40 else None)

    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=provider,
        enable_homeostasis=True, enable_latent=True,
        latent_interval_steps=40, homeostasis_update_interval_steps=10)
    runner.run()
    # Latent summary keys landed as variables.
    assert runner.homeostasis.state.get("unknown_pressure") is not None
    assert runner.homeostasis.state.get(
        "prediction_miss_pressure") is not None


def test_replay_mismatch_raises_pressure():
    regulator = HomeostaticRegulator()
    result = regulator.update({"replay_mismatch": True})
    need = result.need_state.by_type(NeedType.REDUCE_UNCERTAINTY)
    assert need is not None
    assert "replay_mismatch_pressure" in need.source_variables
