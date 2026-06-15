"""DesireMemoryStore: append-only; blocked/failed desires preserved."""

from __future__ import annotations

import os

from solaris_ai_nn.desire_formation import DesireMemoryStore


def test_append_only_records(tmp_path):
    store = DesireMemoryStore(state_dir=str(tmp_path))
    store.record_valence({"valence_id": "V1"})
    store.record_push({"push_id": "P1"})
    store.record_desire({"desire_id": "D1", "status": "candidate"})
    store.record_internal_action({"action_id": "A1", "kind": "shift_attention"})
    store.record_outcome({"outcome_id": "O1"})
    store.write_index()
    for fn in ("valence.jsonl", "pushes.jsonl", "desires.jsonl",
               "internal_actions.jsonl", "outcomes.jsonl",
               "desire_index.json"):
        assert os.path.isfile(tmp_path / fn)


def test_blocked_and_failed_desires_preserved(tmp_path):
    store = DesireMemoryStore(state_dir=str(tmp_path))
    store.record_desire({"desire_id": "D1", "status": "blocked_by_safety"})
    store.record_desire({"desire_id": "D2", "status": "failed"})
    snap = store.snapshot()
    assert snap["blocked_desire_count"] == 1
    assert snap["failed_desire_count"] == 1
    # And the raw records are retrievable (append-only).
    assert len(store.read_records("desire")) == 2


def test_no_op_counted(tmp_path):
    store = DesireMemoryStore(state_dir=str(tmp_path))
    store.record_internal_action({"action_id": "A1", "kind": "no_op"})
    assert store.snapshot()["no_op_count"] == 1
