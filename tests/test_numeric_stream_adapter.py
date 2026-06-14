"""Numeric stream adapter: parse rows, detect spike, warn on malformed."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    NumericStreamAdapter,
    SensorySourceConfig,
)


def _adapter(path):
    return NumericStreamAdapter(SensorySourceConfig(
        source_id="n", source_type="numeric_csv", path=str(path),
        enabled=True))


def test_parses_numeric_rows(tmp_path):
    path = tmp_path / "n.csv"
    path.write_text("ts,value\n1,10\n2,11\n")
    events = [e for e in _adapter(path).poll().events if not e.malformed]
    assert events
    assert events[0].numeric_values.get("value") == 10.0


def test_detects_spike(tmp_path):
    path = tmp_path / "n.csv"
    path.write_text("ts,value\n1,10\n2,11\n3,500\n")
    events = [e for e in _adapter(path).poll().events if not e.malformed]
    trends = [e.metadata.get("trend") for e in events]
    assert "spike" in trends


def test_malformed_row_warning(tmp_path):
    path = tmp_path / "n.csv"
    path.write_text("ts,value\n1,10\noops,bad\n")
    result = _adapter(path).poll()
    assert result.malformed >= 1


def test_trend_labels(tmp_path):
    path = tmp_path / "n.csv"
    path.write_text("ts,value\n1,100\n2,101\n3,50\n4,50\n")
    events = [e for e in _adapter(path).poll().events if not e.malformed]
    trends = [e.metadata.get("trend") for e in events]
    assert "falling" in trends and "stable" in trends
