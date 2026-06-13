"""Integration: the developmental runtime schedules auto-regeneration."""

from __future__ import annotations

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.ecology.nursery import NurseryConfig


def _runtime(tmp_path, mode="safe_auto_repair"):
    config = NurseryConfig(seed=7, duration_steps=160,
                           output_state_dir=str(tmp_path / "eco"))
    return DevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"), simulated_time=True,
        time_acceleration=3600.0, max_steps=160,
        consolidation_interval_steps=40, seed=7,
        enable_ecology=True, nursery_config=config,
        enable_proto_language=True, enable_autoregeneration=True,
        repair_policy_mode=mode)


def test_scheduled_diagnostics_run(tmp_path):
    runtime = _runtime(tmp_path)
    snapshot = runtime.run()
    assert runtime.autoregeneration is not None
    assert runtime.autoregeneration.diagnostics.scans_run >= 1
    assert snapshot["summary"]["autoregeneration"] is not None


def test_first_scan_milestone_recorded(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    fired = {m.type for m in runtime.milestones.registry.milestones}
    assert "first_auto_regeneration_scan" in fired


def test_autoregeneration_in_snapshot(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    assert runtime.snapshot()["autoregeneration"] is not None
