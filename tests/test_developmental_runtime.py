"""Tests for the developmental runtime."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)


def test_short_simulated_run_completes(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        time_acceleration=3600.0, max_steps=100,
        consolidation_interval_steps=50, seed=3)
    snapshot = runtime.run()
    summary = snapshot["summary"]
    assert summary["simulated_time"] is True
    assert summary["developmental_age_hours"] == 100.0
    assert summary["segments_run"] == 2
    assert summary["milestone_count"] >= 1  # 24h survival at least
    assert summary["current_epoch"] != "bootstrapping"


def test_month_year_mode_refused_without_approval(tmp_path):
    with pytest.raises(PermissionError, match="month-scale"):
        DevelopmentalRuntime(state_dir=tmp_path / "m",
                             enable_month_scale=True,
                             max_steps=10).run()
    with pytest.raises(PermissionError, match="year-scale"):
        DevelopmentalRuntime(state_dir=tmp_path / "y",
                             enable_year_scale=True,
                             max_steps=10).run()
    # With explicit governance approval, the gate opens.
    from solaris_ai_nn.governance.policy import GovernancePolicy

    policy = GovernancePolicy()
    policy.permissions.grant("enable_month_scale_testing")
    runtime = DevelopmentalRuntime(state_dir=tmp_path / "ok",
                                   enable_month_scale=True,
                                   max_steps=30,
                                   consolidation_interval_steps=30,
                                   governance=policy, seed=3)
    runtime.run()  # does not raise


def test_unbounded_run_refused(tmp_path):
    with pytest.raises(PermissionError, match="bounded"):
        DevelopmentalRuntime(state_dir=tmp_path / "u",
                             max_steps=None, max_duration_s=None).run()


def test_developmental_state_saved(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=60, consolidation_interval_steps=30, seed=3)
    runtime.run()
    state_path = tmp_path / "dev" / "developmental_state.json"
    assert state_path.exists()
    data = json.loads(state_path.read_text())
    assert data["summary"]["enabled"] is True
    assert (tmp_path / "dev"
            / "autobiographical_memory.jsonl").exists()
    # Clock state survives a second runtime over the same state dir.
    second = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=30, consolidation_interval_steps=30, seed=3)
    assert second.clock.cumulative_lifetime_s > 0


def test_developmental_pressures_exposed(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=50, consolidation_interval_steps=50, seed=3)
    runtime.run()
    pressures = runtime.developmental_pressures()
    for key in ("stagnation_pressure", "drift_pressure",
                "memory_pressure", "consolidation_need",
                "identity_continuity", "long_run_fatigue_proxy"):
        assert key in pressures, key
        assert 0.0 <= float(pressures[key]) <= 1.0
