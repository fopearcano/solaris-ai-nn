"""Integration: the nursery drives a developmental runtime."""

from __future__ import annotations

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.ecology.nursery import NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType


def _runtime(tmp_path, **kw):
    config = NurseryConfig(seed=7, duration_steps=200,
                           output_state_dir=str(tmp_path / "eco"), **kw)
    return DevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"), simulated_time=True,
        time_acceleration=3600.0, max_steps=200,
        consolidation_interval_steps=50, seed=7,
        enable_ecology=True, nursery_config=config)


def test_runtime_runs_with_nursery(tmp_path):
    runtime = _runtime(tmp_path)
    snapshot = runtime.run()
    assert runtime.nursery is not None
    assert snapshot["summary"]["current_epoch"]
    assert runtime.nursery.memory.total_events() > 0


def test_nursery_is_the_stimulus_source(tmp_path):
    runtime = _runtime(tmp_path)
    assert runtime.stimulus_provider == runtime.nursery.stimulus_provider


def test_ecology_in_summary_and_snapshot(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    assert runtime.summary()["ecology"] is not None
    assert runtime.snapshot()["ecology"] is not None


def test_delayed_consequence_milestone_fires(tmp_path):
    runtime = _runtime(
        tmp_path, delayed_consequence_rate=0.3,
        active_regimes=[RegimeType.DELAYED_FEEDBACK_WORLD])
    runtime.run()
    fired = {m.type for m in runtime.milestones.registry.milestones}
    # A delayed-feedback world should produce at least one delayed group,
    # firing the association milestone.
    assert "first_delayed_consequence_association" in fired


def test_episodes_recorded_per_segment(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    assert runtime.nursery.memory.episodes
