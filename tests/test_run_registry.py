"""Tests for the RunRegistry."""

from __future__ import annotations

from solaris_ai_nn.ops.run_manifest import OperationalRunManifest
from solaris_ai_nn.ops.run_registry import RunRegistry


def test_register_start_update_stop(tmp_path):
    registry = RunRegistry(tmp_path / "run_registry.json")
    manifest = OperationalRunManifest(max_steps=50)
    entry = registry.register_start(manifest)
    assert entry["status"] == "running"
    registry.register_update(manifest.run_id, metadata={"last_health": "ok"})
    assert registry.get_run(manifest.run_id)["last_health"] == "ok"
    registry.register_stop(manifest.run_id, graceful=True,
                           summary={"incident_count": 0})
    final = registry.get_run(manifest.run_id)
    assert final["status"] == "stopped"
    assert final["graceful_shutdown"] is True
    assert final["ended_at"] is not None


def test_latest_run_and_listing(tmp_path):
    registry = RunRegistry(tmp_path / "run_registry.json")
    m1 = OperationalRunManifest(max_steps=10)
    m2 = OperationalRunManifest(max_steps=10)
    registry.register_start(m1)
    registry.register_start(m2)
    assert len(registry.list_runs()) == 2
    assert registry.latest_run()["run_id"] == m2.run_id
    assert registry.get_run("nope") is None


def test_registry_serializes(tmp_path):
    registry = RunRegistry(tmp_path / "run_registry.json")
    registry.register_start(OperationalRunManifest(max_steps=10))
    data = registry.to_dict()
    assert "runs" in data and "order" in data
