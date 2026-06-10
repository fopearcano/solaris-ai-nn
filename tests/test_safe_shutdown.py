"""Tests for SafeShutdownManager."""

from __future__ import annotations

import json

from solaris_ai_nn.ops.safe_shutdown import SafeShutdownManager


class _StoppableRunner:
    def __init__(self):
        self.stopped_with = None

    def stop(self, reason):
        self.stopped_with = reason


def test_requests_and_performs_shutdown(tmp_path):
    mgr = SafeShutdownManager(tmp_path / "ops", run_id="r", session_id="s")
    assert not mgr.requested
    mgr.request_shutdown("operator stop")
    assert mgr.requested
    runner = _StoppableRunner()
    record = mgr.perform_shutdown(runner, health_report={"level": "ok"},
                                  inner_map={"x": 1},
                                  final_report_md="# done")
    assert runner.stopped_with == "operator stop"
    assert record["graceful"] is True


def test_writes_shutdown_metadata(tmp_path):
    ops = tmp_path / "ops"
    mgr = SafeShutdownManager(ops, run_id="r1")
    mgr.request_shutdown("watchdog: checkpoint stale")
    mgr.perform_shutdown(health_report={"level": "warning"},
                         final_report_md="# final")
    data = json.loads((ops / "shutdown.json").read_text())
    assert data["reason"] == "watchdog: checkpoint stale"
    assert data["graceful"] is True
    assert (ops / "final_health.json").exists()
    assert (ops / "final_report.md").read_text() == "# final"
    snap = mgr.snapshot()
    assert snap["performed"] is True and snap["requested"] is True
