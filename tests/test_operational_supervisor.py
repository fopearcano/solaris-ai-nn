"""Tests for the OperationalSupervisor."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def _manifest(tmp_path, **kw):
    defaults = dict(mode=RunMode.BOUNDED, max_steps=60,
                    healthcheck_interval_steps=20,
                    state_dir=str(tmp_path / "state"),
                    artifact_dir=str(tmp_path / "ops"), seed=5)
    defaults.update(kw)
    return OperationalRunManifest(**defaults)


def _supervisor(tmp_path, **kw):
    return OperationalSupervisor(
        manifest=_manifest(tmp_path, **kw),
        registry=RunRegistry(tmp_path / "registry.json"))


def test_bounded_supervisor_run_completes(tmp_path):
    start = time.perf_counter()
    sup = _supervisor(tmp_path)
    status = sup.run()
    assert time.perf_counter() - start < 60.0  # no infinite loop
    assert sup._segments_run == 3
    assert (status["telemetry"] or {}).get("lifetime_steps") == 60
    assert (status["health"] or {}).get("level") in ("ok", "warning")


def test_unbounded_run_refused(tmp_path):
    with pytest.raises(ValueError):
        OperationalRunManifest(mode=RunMode.CONTINUOUS_EXPLICIT,
                               state_dir=str(tmp_path / "s"))


def test_health_logs_and_final_files_written(tmp_path):
    sup = _supervisor(tmp_path)
    sup.run()
    ops = sup.ops_dir
    for name in ("manifest.json", "status.json", "status.md", "health.jsonl",
                 "shutdown.json", "artifact_rotation.json", "final_report.md"):
        assert (ops / name).exists(), name
    assert sup.registry.latest_run()["graceful_shutdown"] is True


def test_segment_failure_becomes_incident(tmp_path):
    calls = {"n": 0}

    def exploding_factory(manifest, steps):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("intentional segment failure")
        from solaris_ai_nn.ops.supervisor import default_runner_factory
        return default_runner_factory(manifest, steps)

    sup = OperationalSupervisor(
        manifest=_manifest(tmp_path),
        registry=RunRegistry(tmp_path / "registry.json"),
        runner_factory=exploding_factory)
    status = sup.run()
    types = [i["type"] for i in status["incidents"]]
    assert "checkpoint_failure" in types  # the failure was captured, not raised


def test_operator_stop_honoured(tmp_path):
    sup = _supervisor(tmp_path, max_steps=200, healthcheck_interval_steps=20)
    original = sup._supervise

    def stop_after_first(*args, **kw):
        original(*args, **kw)
        sup.stop("test stop")

    sup._supervise = stop_after_first
    sup.run()
    assert sup._segments_run < 10  # stopped early
    assert sup.shutdown_manager.requested


def test_dry_run_executes_nothing(tmp_path):
    sup = _supervisor(tmp_path, operator_notes="dry")
    sup.dry_run = True
    status = sup.run()
    assert status["telemetry"] is None  # no runner ever built
    assert (sup.ops_dir / "status.json").exists()


def test_operations_summary_for_inner_map(tmp_path):
    sup = _supervisor(tmp_path)
    sup.run()
    summary = sup.operations_summary()
    for key in ("run_mode", "health_level", "watchdog_stop_requested",
                "budget_within", "incident_count",
                "graceful_shutdown_requested", "local_status_server"):
        assert key in summary
