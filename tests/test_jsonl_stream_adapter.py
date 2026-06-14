"""JSONL stream adapter: bounded reads, offset, rotation, no mutation."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import JSONLStreamAdapter, SensorySourceConfig


def _adapter(path, max_events=100):
    return JSONLStreamAdapter(SensorySourceConfig(
        source_id="j", source_type="jsonl_file", path=str(path),
        enabled=True, max_events_per_poll=max_events))


def test_reads_bounded_jsonl(tmp_path):
    path = tmp_path / "e.jsonl"
    path.write_text("".join(f'{{"i":{i}}}\n' for i in range(10)))
    adapter = _adapter(path, max_events=4)
    result = adapter.poll()
    assert len(result.events) == 4  # bounded per poll


def test_malformed_line_skipped(tmp_path):
    path = tmp_path / "e.jsonl"
    path.write_text('{"i":1}\nNOT JSON\n{"i":2}\n')
    result = _adapter(path).poll()
    assert result.malformed == 1
    valid = [e for e in result.events if not e.malformed]
    assert len(valid) == 2


def test_offset_preserved(tmp_path):
    path = tmp_path / "e.jsonl"
    path.write_text('{"i":1}\n')
    adapter = _adapter(path)
    assert len(adapter.poll().events) == 1
    # No new data -> no new events on the next poll.
    assert adapter.poll().events == []
    with open(path, "a") as fh:
        fh.write('{"i":2}\n')
    assert len(adapter.poll().events) == 1


def test_no_file_modification(tmp_path):
    path = tmp_path / "e.jsonl"
    content = '{"i":1}\n{"i":2}\n'
    path.write_text(content)
    _adapter(path).poll()
    assert path.read_text() == content


def test_rotation_detected(tmp_path):
    path = tmp_path / "e.jsonl"
    path.write_text('{"i":1}\n{"i":2}\n{"i":3}\n')
    adapter = _adapter(path)
    adapter.poll()
    # Truncate (rotate) the file; adapter should detect and reset.
    path.write_text('{"i":99}\n')
    result = adapter.poll()
    assert result.rotated is True
    assert len(result.events) == 1
