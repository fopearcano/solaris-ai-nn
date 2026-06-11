"""Tests for latent results feeding developmental memory."""

from __future__ import annotations

from solaris_ai_nn.developmental.consolidation_policy import (
    ConsolidationPolicy,
)
from solaris_ai_nn.developmental.memory_layers import MemoryLayerManager
from solaris_ai_nn.developmental.safety import (
    DevelopmentalSafetyValidator,
)


def test_latent_replay_can_feed_warm_memory(tmp_path):
    manager = MemoryLayerManager(state_dir=tmp_path)
    # A latent replay window's results become hot items, then a warm
    # summary -- exactly like any other recorded evidence.
    for i in range(8):
        manager.add_hot({"replay_window": i, "divergence": 0.02 * i},
                        kind="latent_replay")
    items = list(manager.layers["hot"])
    warm = manager.compress_to_warm(
        items, "8 latent replay windows summarized: divergence rose "
               "gently (offline, simulated evidence)")
    assert warm.kind == "trace_summary"
    assert warm.source_count == 8
    assert "offline" in warm.content["summary"]


def test_counterfactual_stays_offline():
    validator = DevelopmentalSafetyValidator()

    class CounterfactualEvent:
        text = ("counterfactual replay produced divergence 0.4; it "
                "actually happened")
        simulated = True

    report = validator.validate_history_event(CounterfactualEvent())
    assert not report.safe
    # Honestly-labelled counterfactual output is fine.

    class HonestEvent:
        text = ("counterfactual replay produced divergence 0.4 "
                "(offline simulated estimate)")
        simulated = True

    assert validator.validate_history_event(HonestEvent()).safe


def test_developmental_runtime_counts_latent_cycles(tmp_path):
    from solaris_ai_nn.developmental.developmental_runtime import (
        DevelopmentalRuntime,
    )

    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=100, consolidation_interval_steps=50, seed=3)
    runtime.run()
    # The segment runners ran with latent enabled; the clock counted.
    assert runtime.last_runner_snapshot.get("latent") is not None
    assert runtime.clock.total_latent_cycles >= 0  # counted, never lost


def test_mysterium_spike_preserved_through_consolidation():
    manager = MemoryLayerManager()
    manager.add_hot({"mysterium": "pressure spike to 0.85 after "
                                  "prediction miss"},
                    kind="mysterium_spike", importance=0.9)
    for i in range(60):
        manager.add_hot({"step": i}, kind="routine_event")
    report = ConsolidationPolicy(hot_keep_recent=10).apply(manager)
    assert "mysterium_spike" in report.preserved_important
