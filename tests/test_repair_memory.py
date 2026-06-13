"""Tests for repair memory."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.repair_actions import RepairResultClass
from solaris_ai_nn.autoregeneration.repair_memory import (
    RepairMemory,
    RepairRecord,
)


def test_record_writes_jsonl(tmp_path):
    mem = RepairMemory(state_dir=tmp_path)
    mem.record(RepairRecord(repair_id="r1", action_type="compact_memory_layer",
                            scope="memory", applied=True,
                            result_class=RepairResultClass.IMPROVED))
    assert (tmp_path / "repair_memory.jsonl").exists()
    assert mem.snapshot()["record_count"] == 1


def test_before_after_metrics_stored(tmp_path):
    mem = RepairMemory(state_dir=tmp_path)
    rec = mem.record(RepairRecord(
        repair_id="r2", action_type="x", scope="memory", applied=True,
        before_metrics={"size": 100}, after_metrics={"size": 40},
        result_class=RepairResultClass.IMPROVED))
    assert rec.before_metrics["size"] == 100
    assert rec.after_metrics["size"] == 40


def test_rollback_recorded(tmp_path):
    mem = RepairMemory(state_dir=tmp_path)
    mem.record(RepairRecord(repair_id="r3", action_type="x", scope="memory",
                            applied=True, rolled_back=True,
                            result_class=RepairResultClass.ROLLED_BACK))
    assert mem.rollback_count() == 1


def test_success_and_harm_rate(tmp_path):
    mem = RepairMemory(state_dir=tmp_path)
    mem.record(RepairRecord(repair_id="a", action_type="x", scope="memory",
                            applied=True,
                            result_class=RepairResultClass.IMPROVED))
    mem.record(RepairRecord(repair_id="b", action_type="x", scope="memory",
                            applied=True,
                            result_class=RepairResultClass.HARMFUL))
    assert mem.success_rate() == 0.5
    assert mem.harm_rate() == 0.5


def test_refused_counted(tmp_path):
    mem = RepairMemory(state_dir=tmp_path)
    mem.record(RepairRecord(repair_id="c", action_type="x", scope="forbidden",
                            refused=True,
                            result_class=RepairResultClass.REFUSED))
    assert mem.refused_count() == 1
