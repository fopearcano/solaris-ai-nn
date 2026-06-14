"""Folder poll adapter: presence/change detection, no writes, bounded scan."""

from __future__ import annotations

import os

from solaris_ai_nn.sensory_membrane import (
    FolderPollAdapter,
    SensoryModality,
    SensorySourceConfig,
)


def _adapter(folder, **kw):
    return FolderPollAdapter(SensorySourceConfig(
        source_id="f", source_type="folder_poll", path=str(folder),
        enabled=True, **kw))


def test_detects_file_presence(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    adapter = _adapter(tmp_path)
    events = adapter.poll().events
    assert any(e.modality == SensoryModality.FILE_PRESENCE for e in events)


def test_detects_changed_file(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    adapter = _adapter(tmp_path)
    adapter.poll()  # records presence
    import time
    time.sleep(0.01)
    f.write_text("xy changed")
    events = adapter.poll().events
    assert any(e.modality == SensoryModality.FILE_CHANGE for e in events)


def test_no_writes_to_folder(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    before = sorted(os.listdir(tmp_path))
    _adapter(tmp_path).poll()
    assert sorted(os.listdir(tmp_path)) == before


def test_bounded_scan(tmp_path):
    for i in range(10):
        (tmp_path / f"f{i}.txt").write_text("x")
    adapter = _adapter(tmp_path, max_file_count=3, max_events_per_poll=3)
    events = adapter.poll().events
    assert len(events) <= 3


def test_missing_folder_degrades(tmp_path):
    adapter = _adapter(tmp_path / "nope")
    result = adapter.poll()
    assert result.read_errors == 1
