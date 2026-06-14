"""Conscience snapshots: consistent capture and JSON persistence."""

from __future__ import annotations

import json
from pathlib import Path

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    IntegrationHealthMonitor,
    RunContext,
    RunMode,
    SnapshotBuilder,
)


def _orch(tmp_path):
    ctx = RunContext(mode=RunMode.SHORT_DEMO, state_dir=str(tmp_path),
                     max_steps=20,
                     enabled_modules=["bridge", "ecology", "governance",
                                      "world_model"])
    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(ctx)
    orch.initialize()
    for _ in range(10):
        orch.step()
    return orch


def test_build_captures_runtime(tmp_path):
    orch = _orch(tmp_path)
    snap = SnapshotBuilder().build(orch)
    assert snap.run_id == orch.context.run_id
    assert snap.step == orch.step_count
    assert "spine" in snap.payload


def test_build_includes_integration_health(tmp_path):
    orch = _orch(tmp_path)
    snap = SnapshotBuilder().build(orch, IntegrationHealthMonitor())
    assert "integration_health" in snap.payload


def test_persist_writes_json(tmp_path):
    orch = _orch(tmp_path)
    builder = SnapshotBuilder(state_dir=str(tmp_path))
    snap = builder.build(orch)
    path = builder.persist(snap)
    assert path and Path(path).exists()
    data = json.loads(Path(path).read_text())
    assert data["snapshot_id"] == snap.snapshot_id


def test_build_and_persist_records_path(tmp_path):
    orch = _orch(tmp_path)
    builder = SnapshotBuilder(state_dir=str(tmp_path))
    snap = builder.build_and_persist(orch)
    assert snap.payload.get("snapshot_path")
    assert builder.latest() is snap
