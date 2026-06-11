"""Tests for the layered memory."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.developmental.memory_layers import (
    MemoryLayer,
    MemoryLayerManager,
)


def test_hot_warm_cold_fossil_layers_exist():
    manager = MemoryLayerManager()
    assert set(manager.layers) == {"hot", "warm", "cold", "fossil"}
    assert MemoryLayer.ALL == ("hot", "warm", "cold", "fossil")
    for layer in MemoryLayer.ALL:
        assert manager.budgets[layer] > 0


def test_memory_movement_preserves_evidence_summary(tmp_path):
    manager = MemoryLayerManager(state_dir=tmp_path)
    items = [manager.add_hot({"step": i}, kind="routine")
             for i in range(5)]
    warm = manager.compress_to_warm(items, "5 routine events compressed")
    assert warm.evidence_summary == "5 routine events compressed"
    assert warm.source_count == 5
    assert len(manager.layers["hot"]) == 0
    cold = manager.consolidate_to_cold([warm],
                                       "routine pattern schema")
    assert cold.content["schema"] == "routine pattern schema"
    assert cold.source_count == 5  # provenance carried through
    fossil = manager.record_fossil({"description": "first schema"},
                                   kind="first_world_model_schema")
    assert (tmp_path / "fossil_memory.jsonl").exists()
    rows = [json.loads(line) for line in
            (tmp_path / "fossil_memory.jsonl").read_text().splitlines()]
    assert rows[0]["kind"] == "first_world_model_schema"
    # Movements are audited.
    assert len(manager.movement_log) == 3
    assert all(m["evidence_summary"] for m in manager.movement_log)
    del fossil


def test_compression_without_summary_refused():
    manager = MemoryLayerManager()
    item = manager.add_hot({"x": 1})
    with pytest.raises(ValueError, match="evidence summary"):
        manager.compress_to_warm([item], "")
    with pytest.raises(ValueError, match="schema"):
        manager.consolidate_to_cold([item], "")


def test_memory_bounds_enforced():
    manager = MemoryLayerManager(budgets={"hot": 50, "warm": 30,
                                          "cold": 20, "fossil": 10})
    for i in range(120):
        manager.add_hot({"step": i})
    state = manager.state()
    # Hot overflow auto-compressed into warm summaries, never dropped.
    assert state.hot_count <= 50
    assert state.warm_count >= 1
    assert state.raw_events_seen == 120
    assert not state.over_budget
    assert state.compression_ratio() is not None
    assert state.compression_ratio() < 1.0
