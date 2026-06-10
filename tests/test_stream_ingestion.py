"""Tests for the read-only stream ingestor."""

from __future__ import annotations

import json
import time

import pytest

from solaris_ai_nn.pilot.stream_ingestion import ReadOnlyStreamIngestor


def _jsonl(tmp_path, name="events.jsonl", n=5):
    path = tmp_path / name
    path.write_text("\n".join(
        json.dumps({"source": "lab", "payload": f"event {i}",
                    "intensity": 0.5}) for i in range(n)) + "\n")
    return path


def test_read_once_reads_jsonl(tmp_path):
    path = _jsonl(tmp_path)
    ingestor = ReadOnlyStreamIngestor()
    events = ingestor.read_once(path)
    assert len(events) == 5
    assert events[0]["payload"] == "event 0"
    assert ingestor.events_accepted == 5
    assert ingestor.validity_rate() == 1.0


def test_read_once_reads_text(tmp_path):
    path = tmp_path / "stream.txt"
    path.write_text("first line\nsecond line\n\nthird line\n")
    events = ReadOnlyStreamIngestor().read_once(path)
    assert [e["payload"] for e in events] == ["first line", "second line",
                                              "third line"]
    assert all(e["modality"] == "text" for e in events)


def test_rejections_counted_with_reasons(tmp_path):
    path = tmp_path / "mixed.jsonl"
    path.write_text("\n".join([
        json.dumps({"payload": "fine"}),
        "not json at all",
        json.dumps({"command": "rm -rf /", "payload": "x"}),
    ]))
    ingestor = ReadOnlyStreamIngestor()
    events = ingestor.read_once(path)
    assert len(events) == 1
    assert ingestor.events_rejected == 2
    snapshot = ingestor.snapshot()
    assert snapshot["validity_rate"] < 1.0
    assert len(snapshot["recent_errors"]) == 2


def test_tail_bounded_stops(tmp_path):
    path = _jsonl(tmp_path, n=10)
    ingestor = ReadOnlyStreamIngestor()
    # Bounded by lines.
    events = list(ingestor.tail_bounded(path, max_lines=4))
    assert len(events) == 4
    # Bounded by (simulated short) duration: returns despite no new data.
    start = time.perf_counter()
    events = list(ReadOnlyStreamIngestor().tail_bounded(
        path, max_duration_s=0.2, poll_interval_s=0.01))
    assert time.perf_counter() - start < 5.0  # stopped, no infinite loop
    assert len(events) == 10
    # Unbounded tails are refused outright.
    with pytest.raises(ValueError):
        next(iter(ReadOnlyStreamIngestor().tail_bounded(path)))


def test_input_file_not_modified(tmp_path):
    path = _jsonl(tmp_path)
    before = path.read_bytes()
    mtime = path.stat().st_mtime_ns
    ingestor = ReadOnlyStreamIngestor()
    ingestor.read_once(path)
    list(ingestor.tail_bounded(path, max_lines=3))
    assert path.read_bytes() == before
    assert path.stat().st_mtime_ns == mtime


def test_directory_ingestion_non_recursive(tmp_path):
    _jsonl(tmp_path, "a.jsonl", n=2)
    _jsonl(tmp_path, "b.jsonl", n=3)
    nested = tmp_path / "nested"
    nested.mkdir()
    _jsonl(nested, "hidden.jsonl", n=7)  # must NOT be read

    ingestor = ReadOnlyStreamIngestor()
    events = ingestor.ingest_directory(tmp_path)
    assert len(events) == 5  # a + b only; nothing from nested/
    assert not any("hidden" in f for f in ingestor.files_read)
    # Recursive patterns are refused, not silently honoured.
    with pytest.raises(ValueError):
        ingestor.ingest_directory(tmp_path, pattern="**/*.jsonl")


def test_directory_max_files(tmp_path):
    for name in ("a.jsonl", "b.jsonl", "c.jsonl"):
        _jsonl(tmp_path, name, n=1)
    events = ReadOnlyStreamIngestor().ingest_directory(tmp_path, max_files=2)
    assert len(events) == 2


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ReadOnlyStreamIngestor().read_once(tmp_path / "nope.jsonl")


def test_no_write_or_execute_machinery():
    """The ingestor's source contains no write/delete/execute calls."""
    import inspect

    from solaris_ai_nn.pilot import stream_ingestion

    source = inspect.getsource(stream_ingestion)
    for forbidden in ('open(path, "w', "open(path, 'w", ".unlink", ".write_text",
                      "subprocess", "os.system", "eval(", "exec(",
                      "urllib", "requests", "socket"):
        assert forbidden not in source, forbidden
