"""Tests for exploration memory."""

from __future__ import annotations

from solaris_ai_nn.active_perception.exploration_memory import (
    ExplorationMemory,
    ExplorationOutcome,
    ExplorationRecord,
)


def test_record_writes_jsonl(tmp_path):
    memory = ExplorationMemory(state_dir=tmp_path)
    memory.record(ExplorationRecord(
        action_id="SMP_1", action_type="look",
        outcome=ExplorationOutcome.USEFUL))
    assert (tmp_path / "exploration_memory.jsonl").exists()
    assert memory.snapshot()["record_count"] == 1


def test_useful_and_blocked_outcomes_stored(tmp_path):
    memory = ExplorationMemory(state_dir=tmp_path)
    memory.record(ExplorationRecord(action_id="a", action_type="look",
                                    outcome=ExplorationOutcome.USEFUL))
    memory.record(ExplorationRecord(action_id="b", action_type="look",
                                    outcome=ExplorationOutcome.BLOCKED))
    assert memory.useful_rate() == 0.5
    assert memory.blocked_count() == 1


def test_bounded_records():
    memory = ExplorationMemory(state_dir=None, max_records=5)
    for i in range(20):
        memory.record(ExplorationRecord(action_id=str(i),
                                        action_type="look"))
    assert len(memory.records) == 5


def test_unknown_outcome_normalized():
    record = ExplorationRecord(action_id="x", action_type="look",
                               outcome="bogus")
    assert record.outcome == ExplorationOutcome.UNKNOWN


def test_persist_policy_and_attention_state(tmp_path):
    memory = ExplorationMemory(state_dir=tmp_path)
    memory.save_policy_state({"mode": "balanced"})
    memory.save_attention_state({"current": None})
    assert (tmp_path / "sampling_policy_state.json").exists()
    assert (tmp_path / "attention_state.json").exists()


def test_snapshot_serializes(tmp_path):
    memory = ExplorationMemory(state_dir=tmp_path)
    memory.record(ExplorationRecord(action_id="a", action_type="rest"))
    snap = memory.snapshot()
    assert snap["record_count"] == 1
    assert "outcome_counts" in snap
