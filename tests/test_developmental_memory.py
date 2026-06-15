"""DevelopmentalMemoryStore: append-only; regressions/plateaus/inconclusive kept."""

from __future__ import annotations

import os

from solaris_ai_nn.developmental_life import DevelopmentalMemoryStore


def test_append_only_records(tmp_path):
    store = DevelopmentalMemoryStore(state_dir=str(tmp_path))
    store.record_life_cycle({"phase": "boot"})
    store.record_epoch({"epoch_id": "E1"})
    store.record_growth_state({"composite": 0.5})
    store.record_maturation({"marker_id": "M1"})
    store.record_phase_transition({"transition_id": "T1"})
    store.record_plateau({"plateau_id": "P1"})
    store.record_regression({"regression_id": "R1"})
    store.write_index()
    for fn in ("life_cycle.jsonl", "epochs.jsonl", "growth_state.jsonl",
               "maturation_markers.jsonl", "phase_transitions.jsonl",
               "plateaus.jsonl", "regressions.jsonl",
               "developmental_index.json"):
        assert os.path.isfile(tmp_path / fn)


def test_regression_and_plateau_preserved(tmp_path):
    store = DevelopmentalMemoryStore(state_dir=str(tmp_path))
    store.record_regression({"regression_id": "R1", "reason": "prediction"})
    store.record_plateau({"plateau_id": "P1", "reason": "no_new_concepts"})
    snap = store.snapshot()
    assert snap["regression_count"] == 1
    assert snap["plateau_count"] == 1
    assert len(store.read_records("regression")) == 1
    assert len(store.read_records("plateau")) == 1


def test_inconclusive_preserved(tmp_path):
    store = DevelopmentalMemoryStore(state_dir=str(tmp_path))
    store.record_phase_transition({"transition_id": "T1", "inconclusive": True})
    records = store.read_records("phase_transition")
    assert records and records[0]["payload"]["inconclusive"] is True


def test_load_index_survives_restart(tmp_path):
    store = DevelopmentalMemoryStore(state_dir=str(tmp_path))
    store.record_epoch({"epoch_id": "E1"})
    store.record_regression({"regression_id": "R1"})
    store.write_index()
    fresh = DevelopmentalMemoryStore(state_dir=str(tmp_path))
    idx = fresh.load_index()
    assert idx.regression_count == 1
    assert "E1" in idx.epoch_ids
