"""Tests for the HealthMonitor."""

from __future__ import annotations

import time

from solaris_ai_nn.ops.health import HealthMonitor


def _good_snapshot(tmp_path):
    (tmp_path / "latest_checkpoint.json").write_text("{}")
    now = time.time()
    return {
        "now": now,
        "lifecycle": {"alive": True, "state": "running",
                      "last_heartbeat_ts": now - 1,
                      "last_checkpoint_ts": now - 5},
        "telemetry": {"events": 10, "reservoir_updates": 10,
                      "trace_event_count": 10, "memory_trace_length": 10},
        "substrate": {"state_norm": 4.0, "drift": 0.5},
        "state_dir": str(tmp_path),
    }


def test_ok_health_from_good_snapshot(tmp_path):
    report = HealthMonitor().check(_good_snapshot(tmp_path))
    assert report.level == "ok"
    assert report.issues() == []
    assert "level" in report.to_dict()
    assert report.to_markdown().startswith("## Health report")


def test_warning_on_stale_heartbeat(tmp_path):
    snap = _good_snapshot(tmp_path)
    snap["lifecycle"]["last_heartbeat_ts"] = time.time() - 1000
    report = HealthMonitor().check(snap)
    assert report.level == "warning"
    assert any("heartbeat" in c.name for c in report.issues())


def test_critical_on_nan_substrate_norm(tmp_path):
    snap = _good_snapshot(tmp_path)
    snap["substrate"]["state_norm"] = float("nan")
    report = HealthMonitor().check(snap)
    assert report.level == "critical"
    assert any(c.name == "state_finite" for c in report.issues())


def test_runaway_activity_is_critical(tmp_path):
    snap = _good_snapshot(tmp_path)
    snap["substrate"]["state_norm"] = 1e6
    assert HealthMonitor().check(snap).level == "critical"


def test_persistence_failure_reported(tmp_path):
    snap = _good_snapshot(tmp_path)
    snap["state_dir"] = str(tmp_path / "does_not_exist")
    report = HealthMonitor().check(snap)
    assert any(c.domain == "persistence" and c.status == "critical"
               for c in report.checks)


def test_frozen_counters_warn_on_second_check(tmp_path):
    monitor = HealthMonitor()
    snap = _good_snapshot(tmp_path)
    assert monitor.check(snap).level == "ok"
    report = monitor.check(snap)  # identical counters: frozen
    assert report.level == "warning"
    assert any("frozen" in c.detail for c in report.issues())
