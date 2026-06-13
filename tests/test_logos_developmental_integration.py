"""Integration: the developmental runtime schedules LOGOS scans."""

from __future__ import annotations

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.ecology.nursery import NurseryConfig


def _runtime(tmp_path):
    config = NurseryConfig(seed=7, duration_steps=160,
                           output_state_dir=str(tmp_path / "eco"))
    return DevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"), simulated_time=True,
        time_acceleration=3600.0, max_steps=160,
        consolidation_interval_steps=40, seed=7,
        enable_ecology=True, nursery_config=config,
        enable_proto_language=True, enable_logos_complexity=True)


def test_logos_scan_scheduled(tmp_path):
    runtime = _runtime(tmp_path)
    snapshot = runtime.run()
    assert runtime.logos is not None
    assert runtime.logos.fracture.scans_run >= 1
    assert snapshot["summary"]["logos"] is not None


def test_logos_milestone_recorded(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    fired = {m.type for m in runtime.milestones.registry.milestones}
    assert "first_logos_tension" in fired


def test_logos_in_snapshot(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    assert runtime.snapshot()["logos"] is not None
