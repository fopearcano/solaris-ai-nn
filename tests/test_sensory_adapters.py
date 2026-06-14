"""Sensory adapter contract: read-only, malformed-tolerant, provenanced."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    AdapterResult,
    JSONLStreamAdapter,
    SensorySourceConfig,
)


def test_adapter_contract_poll(tmp_path):
    path = tmp_path / "e.jsonl"
    path.write_text('{"a":1}\n{"a":2}\n')
    adapter = JSONLStreamAdapter(SensorySourceConfig(
        source_id="j", source_type="jsonl_file", path=str(path),
        enabled=True))
    result = adapter.poll()
    assert isinstance(result, AdapterResult)
    assert len(result.events) == 2
    adapter.close()
    assert adapter.poll().events == []


def test_malformed_payload_handled(tmp_path):
    path = tmp_path / "e.jsonl"
    path.write_text('{"a":1}\n{bad}\n')
    adapter = JSONLStreamAdapter(SensorySourceConfig(
        source_id="j", source_type="jsonl_file", path=str(path),
        enabled=True))
    result = adapter.poll()
    assert result.malformed == 1
    # The malformed line is still emitted as a flagged event, never raised.
    assert any(e.malformed for e in result.events)


def test_missing_source_degrades(tmp_path):
    adapter = JSONLStreamAdapter(SensorySourceConfig(
        source_id="j", source_type="jsonl_file",
        path=str(tmp_path / "nope.jsonl"), enabled=True))
    result = adapter.poll()
    assert result.read_errors == 1
    assert result.events == []


def test_provenance_basis(tmp_path):
    path = tmp_path / "e.jsonl"
    path.write_text('{"a":1}\n')
    adapter = JSONLStreamAdapter(SensorySourceConfig(
        source_id="j", source_type="jsonl_file", path=str(path),
        enabled=True))
    event = adapter.poll().events[0]
    assert event.event_hash.startswith("sha256:")
    assert event.adapter_name == "jsonl_stream_adapter"
