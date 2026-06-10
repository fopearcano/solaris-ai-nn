"""Tests for the sleep cycle."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.latent.latent_memory import LatentMemoryStore
from solaris_ai_nn.latent.sleep_cycle import SleepCycle
from solaris_ai_nn.signals import canonical as C


def _bridge(steps=30):
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(steps):
        bridge.process(C.Stimulus(payload=f"p{i % 3}", intensity=0.5))
        bridge.react(C.Reaction(valence=1.0 if i % 2 == 0 else -0.5))
    return bridge


def test_bounded_sleep_cycle_runs(tmp_path):
    bridge = _bridge()
    cycle = SleepCycle(bridge=bridge, store=LatentMemoryStore(tmp_path))
    start = time.perf_counter()
    result = cycle.run(max_steps=10)
    assert time.perf_counter() - start < 30.0  # bounded, no infinite loop
    assert 0 < result.steps_run <= 10
    assert result.offline
    with pytest.raises(ValueError):
        cycle.run(max_steps=0)  # unbounded/invalid bound rejected


def test_no_external_actions_executed(tmp_path):
    bridge = _bridge()
    steps_before = bridge.telemetry.steps
    actions_before = len([r for r in bridge.trace.records
                          if r.category == "action"])
    cycle = SleepCycle(bridge=bridge, store=LatentMemoryStore(tmp_path))
    result = cycle.run(max_steps=10)
    assert result.external_actions_executed == 0
    # The bridge processed nothing new: no signals, no new action records.
    assert bridge.telemetry.steps == steps_before
    assert len([r for r in bridge.trace.records
                if r.category == "action"]) == actions_before


def test_consolidation_report_produced(tmp_path):
    bridge = _bridge(40)
    store = LatentMemoryStore(tmp_path)
    cycle = SleepCycle(bridge=bridge, store=store)
    result = cycle.run(max_steps=8)
    assert result.consolidation  # a ConsolidationReport dict
    assert result.consolidation.get("events_considered", 0) > 0
    assert result.schemas_created > 0
    assert store.snapshot()["schema_count"] == result.schemas_created
    assert all("pattern" in s for s in result.schema_summaries)
    record = store.cycles()[-1]
    assert record["cycle_type"] == "sleep"
    assert record["offline"] is True


def test_high_activity_stabilizes(tmp_path):
    bridge = _bridge()
    # Inflate the substrate state far beyond the stabilization threshold.
    bridge.substrate.set_state([10.0] * bridge.substrate.state_size)
    cycle = SleepCycle(bridge=bridge, store=LatentMemoryStore(tmp_path),
                       stabilize_above_norm=5.0)
    result = cycle.run(max_steps=50)
    assert result.stabilized
    assert result.activity_after < result.activity_before
    assert result.steps_run <= 50


def test_snapshot_counts_cycles(tmp_path):
    cycle = SleepCycle(bridge=_bridge(), store=LatentMemoryStore(tmp_path))
    cycle.run(5)
    cycle.run(5)
    snap = cycle.snapshot()
    assert snap["cycles_run"] == 2
    assert snap["external_actions_executed"] == 0
