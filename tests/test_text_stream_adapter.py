"""Text stream adapter: text as environmental stimulus, not a command."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    SensoryModality,
    SensorySourceConfig,
    TextStreamAdapter,
)


def _adapter(path):
    return TextStreamAdapter(SensorySourceConfig(
        source_id="t", source_type="text_file", path=str(path), enabled=True))


def test_reads_text_as_environmental_stimulus(tmp_path):
    path = tmp_path / "log.txt"
    path.write_text("a bird sings\nthe wind rises\n")
    events = _adapter(path).poll().events
    assert len(events) == 2
    assert all(e.modality == SensoryModality.TEXTUAL for e in events)


def test_text_not_command(tmp_path):
    path = tmp_path / "log.txt"
    path.write_text("rm -rf /\nshutdown now\n")
    events = _adapter(path).poll().events
    for e in events:
        assert e.metadata.get("is_operator_command") is False
        assert e.metadata.get("classification") == "textual_environmental_stimulus"


def test_raw_hash_stored(tmp_path):
    path = tmp_path / "log.txt"
    path.write_text("hello\n")
    event = _adapter(path).poll().events[0]
    assert event.raw_line == "hello"
    assert event.event_hash.startswith("sha256:")


def test_blank_lines_skipped(tmp_path):
    path = tmp_path / "log.txt"
    path.write_text("one\n\n\ntwo\n")
    assert len(_adapter(path).poll().events) == 2
