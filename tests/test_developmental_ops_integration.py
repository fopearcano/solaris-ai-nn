"""Tests for ops supervision over the developmental runtime."""

from __future__ import annotations

import inspect

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_ops_status_includes_epoch_memory_drift(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=60, consolidation_interval_steps=30, seed=3)
    runtime.run()
    summary = runtime.summary()
    for key in ("enabled", "current_epoch", "clock", "memory_layers",
                "last_consolidation_at_s", "last_milestone",
                "growth_status", "drift_status",
                "next_long_report_after_steps"):
        assert key in summary, key
    # The supervisor health snapshot picks this up via the runner.
    source = inspect.getsource(OperationalSupervisor._health_snapshot)
    assert 'getattr(runner, "developmental", None)' in source
    assert 'snapshot["developmental"] = developmental.summary()' \
        in source


def test_health_warning_for_memory_budget():
    """The supervisor monitoring block warns on over-budget memory."""
    source = inspect.getsource(OperationalSupervisor._supervise)
    block = source.split("Developmental monitoring")[1].split(
        "LLM adapter monitoring")[0]
    assert "over_budget" in block
    assert "stagnation_windows" in block
    assert "fast_warning" in block
    # Evidence only: the developmental block never requests a stop.
    assert "request_shutdown" not in block
    assert "_stop_requested" not in block
