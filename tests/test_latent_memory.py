"""Tests for latent memory persistence."""

from __future__ import annotations

import json

from solaris_ai_nn.latent.latent_memory import (
    ConsolidatedSchema,
    DreamTrace,
    LatentMemoryRecord,
    LatentMemoryStore,
    ReplayTrace,
)


def test_latent_memory_writes_jsonl(tmp_path):
    store = LatentMemoryStore(tmp_path)
    record = store.record_cycle(LatentMemoryRecord(
        cycle_type="sleep", steps_run=10,
        replayed_window_ids=["w-1"], counterfactual_kinds=["invert_valence"],
        substrate_response={"norm": 1.2},
        prediction_results={"hits": 3},
        mysterium_change=-0.04,
        schema_summaries=["pattern 'x' -> 'a'"],
        offline_suggestions=[{"target": "readout.learning_rate"}],
        production_mutated=False))
    assert record.offline is True
    rows = [json.loads(line) for line in
            (tmp_path / "latent_memory.jsonl").read_text().splitlines()]
    assert rows[0]["cycle_type"] == "sleep"
    assert rows[0]["offline"] is True
    assert rows[0]["production_mutated"] is False
    assert store.cycles() == rows


def test_dream_and_replay_traces_persist(tmp_path):
    store = LatentMemoryStore(tmp_path)
    store.record_dream(DreamTrace(window_id="w-1",
                                  counterfactual_kind="invert_valence",
                                  events_replayed=8,
                                  divergence={"score": 0.3}))
    store.record_replay(ReplayTrace(window_id="w-1", strategy="recent",
                                    events_replayed=8, seed=7))
    assert (tmp_path / "dream_traces.jsonl").exists()
    assert (tmp_path / "replay_traces.jsonl").exists()
    dream = store.dreams()[0]
    assert dream["offline"] is True and dream["simulated"] is True
    replay = store.replays()[0]
    assert replay["offline"] is True
    assert replay["mutated_production"] is False


def test_consolidated_schemas_serialize(tmp_path):
    store = LatentMemoryStore(tmp_path)
    schema = ConsolidatedSchema(pattern="Stimulus:2",
                                dominant_action="approach",
                                support_count=5, average_valence=0.7)
    store.upsert_schema(schema)
    assert "Stimulus:2" in schema.summary()
    data = json.loads((tmp_path / "consolidated_schemas.json").read_text())
    assert data["schemas"][0]["pattern"] == "Stimulus:2"

    # Upsert keeps one entry per pattern (refreshed, not duplicated)...
    store.upsert_schema(ConsolidatedSchema(pattern="Stimulus:2",
                                           dominant_action="approach",
                                           support_count=9))
    assert len(store.schemas()) == 1
    assert store.schemas()[0].support_count == 9
    # ...and a fresh store loads them back.
    reloaded = LatentMemoryStore(tmp_path)
    assert reloaded.schemas()[0].pattern == "Stimulus:2"
    assert reloaded.schemas()[0].schema_id == schema.schema_id


def test_snapshot_counts(tmp_path):
    store = LatentMemoryStore(tmp_path)
    store.record_cycle(LatentMemoryRecord(cycle_type="dream"))
    store.record_dream(DreamTrace(window_id="w", counterfactual_kind="x"))
    store.upsert_schema(ConsolidatedSchema(pattern="p"))
    snap = store.snapshot()
    assert snap["cycle_count"] == 1
    assert snap["dream_count"] == 1
    assert snap["schema_count"] == 1
    assert snap["paths"]["latent_memory"].endswith("latent_memory.jsonl")
