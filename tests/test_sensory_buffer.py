"""Sensory buffer: dedup, ordering, batching, JSONL persistence."""

from __future__ import annotations

import os

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryBuffer,
    SensoryEventNormalizer,
)


def _norm(payload, source="s"):
    return SensoryEventNormalizer().normalize(
        RawSensoryEvent(source_id=source, source_type="text_file",
                        payload=payload))


def test_buffer_deduplicates(tmp_path):
    buf = SensoryBuffer(state_dir=str(tmp_path))
    norm = SensoryEventNormalizer()
    raw = RawSensoryEvent(source_id="s", source_type="text_file",
                          payload="same")
    assert buf.admit(norm.normalize(raw)) is True
    # Same recurrence key within the window -> duplicate, not admitted.
    assert buf.admit(norm.normalize(
        RawSensoryEvent(source_id="s", source_type="text_file",
                        payload="same"))) is False
    assert buf.duplicate_count == 1


def test_writes_jsonl(tmp_path):
    buf = SensoryBuffer(state_dir=str(tmp_path))
    buf.admit(_norm("a"))
    assert os.path.exists(str(tmp_path / "sensory_events.jsonl"))
    assert os.path.exists(str(tmp_path / "sensory_buffer.jsonl"))


def test_capacity_drops_oldest(tmp_path):
    buf = SensoryBuffer(state_dir=str(tmp_path), capacity=2)
    for i in range(5):
        buf.admit(_norm(f"v{i}"))
    assert buf.dropped_count >= 1
    assert buf.pending() <= 2


def test_emit_batch_preserves_order(tmp_path):
    buf = SensoryBuffer(state_dir=str(tmp_path), max_per_batch=10)
    for i in range(3):
        buf.admit(_norm(f"v{i}"))
    batch = buf.emit_batch()
    summaries = [e["payload_summary"] for e in batch]
    assert summaries == ["v0", "v1", "v2"]


def test_snapshot_counts(tmp_path):
    buf = SensoryBuffer(state_dir=str(tmp_path))
    buf.admit(_norm("a"))
    snap = buf.snapshot()
    assert snap["admitted_count"] == 1
