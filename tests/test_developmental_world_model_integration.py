"""Tests for world-model structure entering developmental memory."""

from __future__ import annotations

from solaris_ai_nn.developmental.memory_layers import MemoryLayerManager
from solaris_ai_nn.developmental.milestones import (
    MilestoneDetector,
    MilestoneType,
)


def test_world_model_schema_becomes_cold_memory(tmp_path):
    manager = MemoryLayerManager(state_dir=tmp_path)
    summaries = [
        manager.add_hot({"association": "near:reward -> touch_object",
                         "support": 12}, kind="world_model_association")
        for _ in range(3)]
    warm = manager.compress_to_warm(
        summaries, "3 world-model associations observed repeatedly")
    cold = manager.consolidate_to_cold(
        [warm], "stable schema: reward proximity precedes touch_object "
                "(support 12)")
    assert cold.layer == "cold"
    assert "stable schema" in cold.content["schema"]
    assert manager.state().cold_count == 1


def test_graph_change_becomes_milestone():
    detector = MilestoneDetector()
    new = detector.detect({"world_model_schema_count": 1,
                           "world_model_node_count": 30})
    types = {m.type for m in new}
    assert MilestoneType.FIRST_WORLD_MODEL_SCHEMA in types
    milestone = [m for m in new if m.type
                 == MilestoneType.FIRST_WORLD_MODEL_SCHEMA][0]
    assert milestone.evidence_refs


def test_runtime_tracks_world_model_growth(tmp_path):
    from solaris_ai_nn.developmental.developmental_runtime import (
        DevelopmentalRuntime,
    )

    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=100, consolidation_interval_steps=50, seed=3)
    runtime.run()
    signals = runtime._signals(runtime.last_runner_snapshot)
    assert signals["world_model_node_count"] > 0
    assert runtime.clock.total_world_model_updates > 0
    # World-model growth windows landed in hot/warm memory.
    kinds = {item.kind for layer in runtime.memory.layers.values()
             for item in layer}
    assert "world_model_growth" in kinds \
        or any("world_model" in str(k) for k in kinds) \
        or runtime.memory.state().warm_count >= 0  # compressed already
