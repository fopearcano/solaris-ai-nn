"""Pilot-1 observability: JSONL append, metric collection, restart survival."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot1 import (
    METRIC_KEYS,
    ObservationEvent,
    PilotObservabilityCollector,
)


def test_event_writes_jsonl(tmp_path):
    col = PilotObservabilityCollector(base_dir=str(tmp_path))
    col.heartbeat()
    assert os.path.exists(col.obs_path)
    assert col.stream.count == 1


def test_metrics_collected(tmp_path):
    col = PilotObservabilityCollector(base_dir=str(tmp_path))
    metrics = col.observe(snapshot={"structural_change_score": 0.2,
                                    "proto_symbol_count": 5,
                                    "bus_message_count": 30})
    for key in METRIC_KEYS:
        assert key in metrics
    assert metrics["structural_change_score"] == 0.2


def test_incidents_never_hidden(tmp_path):
    col = PilotObservabilityCollector(base_dir=str(tmp_path))
    col.record_incident("safety", "critical", "boom")
    assert os.path.exists(col.incidents_path)


def test_survives_restart_append(tmp_path):
    col1 = PilotObservabilityCollector(base_dir=str(tmp_path))
    col1.observe(snapshot={"structural_change_score": 0.1})
    # A second collector over the same dir appends, not truncates.
    col2 = PilotObservabilityCollector(base_dir=str(tmp_path), restart_count=1)
    col2.observe(snapshot={"structural_change_score": 0.2})
    rows = col2.stream.read_all()
    assert len(rows) >= 2


def test_derived_signals(tmp_path):
    col = PilotObservabilityCollector(base_dir=str(tmp_path))
    col.observe(snapshot={"structural_change_score": 0.0})
    m = col.observe(snapshot={"structural_change_score": 0.5})
    assert m["drift_velocity"] >= 0.0
    assert "stagnation_seconds" in m


def test_daily_rollup(tmp_path):
    col = PilotObservabilityCollector(base_dir=str(tmp_path))
    col.observe(snapshot={"structural_change_score": 0.1})
    rollup = col.write_daily_rollup(1)
    assert rollup["day"] == 1
    assert os.path.exists(col.daily_path)
