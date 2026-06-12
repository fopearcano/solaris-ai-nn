"""Tests for proto-language inside the developmental runtime."""

from __future__ import annotations

import json

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)


def _runtime(tmp_path, steps=100):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        time_acceleration=3600.0, max_steps=steps,
        consolidation_interval_steps=50, seed=3,
        enable_proto_language=True)
    runtime.run()
    return runtime


def test_first_symbol_milestone_recorded(tmp_path):
    runtime = _runtime(tmp_path)
    types = {m.type for m in runtime.milestones.registry.milestones}
    assert "first_proto_symbol" in types
    milestone = [m for m in runtime.milestones.registry.milestones
                 if m.type == "first_proto_symbol"][0]
    assert milestone.evidence_refs
    assert "not human language" in milestone.description
    # Symbol births fossilized.
    fossil_rows = (tmp_path / "dev" / "fossil_memory.jsonl"
                   ).read_text().splitlines()
    assert any("proto_symbol_birth" in row for row in fossil_rows)


def test_symbol_survival_tracked_over_simulated_time(tmp_path):
    runtime = _runtime(tmp_path, steps=150)
    layer = runtime.protolanguage
    assert layer.registry.snapshot()["symbol_count"] >= 1
    # Birth events landed in symbol memory across segments.
    memory_path = tmp_path / "dev" / "symbol_memory.jsonl"
    assert memory_path.exists()
    rows = [json.loads(line)
            for line in memory_path.read_text().splitlines()]
    assert any(row["event"] == "birth" for row in rows)
    # The registry persisted and survives a second runtime.
    assert (tmp_path / "dev" / "proto_symbols.json").exists()
    second = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=50, consolidation_interval_steps=50, seed=3,
        enable_proto_language=True)
    assert second.protolanguage is not None


def test_proto_language_in_developmental_summary(tmp_path):
    runtime = _runtime(tmp_path)
    summary = runtime.summary()
    proto = summary["proto_language"]
    assert proto is not None
    assert proto["enabled"] is True
    assert proto["symbol_count"] >= 1
    assert proto["authority"] is False


def test_disabled_by_default(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "plain", simulated_time=True,
        max_steps=50, consolidation_interval_steps=50, seed=3)
    runtime.run()
    assert runtime.protolanguage is None
    assert runtime.summary()["proto_language"] is None
