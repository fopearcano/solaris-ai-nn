"""CognitiveMemoryStore: append-only; failed predictions/ambiguity preserved."""

from __future__ import annotations

import os

from solaris_ai_nn.sensorium_cognition import CognitiveMemoryStore


def test_append_only_records(tmp_path):
    store = CognitiveMemoryStore(state_dir=str(tmp_path))
    store.record_move({"move_id": "M1", "move_type": "predict_next_sign"})
    store.record_prediction({"prediction_id": "P1", "outcome": "unknown"})
    store.record_simulation({"simulation_id": "S1"})
    store.write_index()
    assert os.path.isfile(tmp_path / "cognitive_moves.jsonl")
    assert os.path.isfile(tmp_path / "predictions.jsonl")
    assert os.path.isfile(tmp_path / "simulations.jsonl")
    assert os.path.isfile(tmp_path / "cognitive_index.json")


def test_failed_predictions_preserved(tmp_path):
    store = CognitiveMemoryStore(state_dir=str(tmp_path))
    store.record_prediction({"prediction_id": "P1", "outcome": "failure"})
    store.record_prediction({"prediction_id": "P2", "outcome": "success"})
    # The failed prediction is indexed and kept in the append-only log.
    assert "P1" in store.index.failed_prediction_ids
    records = store.read_records("prediction")
    assert len(records) == 2


def test_ambiguity_preserved(tmp_path):
    store = CognitiveMemoryStore(state_dir=str(tmp_path))
    store.record_question({"pressure_id": "Q1",
                           "pressure_type": "unstable_relation"})
    records = store.read_records("question")
    assert len(records) == 1
    assert records[0]["payload"]["pressure_type"] == "unstable_relation"


def test_index_counts(tmp_path):
    store = CognitiveMemoryStore(state_dir=str(tmp_path))
    store.record_move({"move_id": "M1"})
    store.record_move({"move_id": "M2"})
    store.record_synthesis({"synthesis_id": "Y1"})
    snap = store.snapshot()
    assert snap["counts"]["move"] == 2
    assert snap["counts"]["synthesis"] == 1
