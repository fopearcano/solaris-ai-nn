"""ReactionMemoryStore: append-only; failed/blocked/no-effect preserved."""

from __future__ import annotations

import os

from solaris_ai_nn.action_reaction import ReactionMemoryStore


def test_append_only_memory(tmp_path):
    store = ReactionMemoryStore(state_dir=str(tmp_path))
    store.record_action({"action_id": "A1", "kind": "shift_attention"})
    store.record_reaction({"reaction_id": "R1", "kind": "uncertainty_reduced"})
    store.record_consequence({"consequence_id": "C1"})
    store.record_effect({"action_kind": "shift_attention"})
    store.record_habit({"habit_id": "H1"})
    store.record_inhibition({"inhibition_id": "I1"})
    store.record_policy_update({"update_id": "P1"})
    store.write_index()
    for fn in ("actions.jsonl", "reactions.jsonl", "consequences.jsonl",
               "effects.jsonl", "habits.jsonl", "inhibitions.jsonl",
               "policy_updates.jsonl", "action_reaction_index.json"):
        assert os.path.isfile(tmp_path / fn)


def test_blocked_and_no_effect_preserved(tmp_path):
    store = ReactionMemoryStore(state_dir=str(tmp_path))
    store.record_action({"action_id": "A1", "kind": "actuate_robot",
                         "is_forbidden": True, "status": "blocked"})
    store.record_action({"action_id": "A2", "kind": "no_op"})
    store.record_reaction({"reaction_id": "R1", "kind": "no_effect",
                          "action_ref": "A3"})
    snap = store.snapshot()
    assert snap["blocked_action_count"] == 1
    assert snap["no_op_count"] == 1
    assert snap["no_effect_action_count"] == 1
    assert len(store.read_records("action")) == 2
