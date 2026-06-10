"""Tests for the pilot registry."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.pilot.pilot_manifest import PilotManifest
from solaris_ai_nn.pilot.pilot_registry import PilotRegistry


def _manifest(tmp_path, **kw):
    defaults = dict(profile="simulated", operator="tester",
                    state_dir=str(tmp_path / "state"),
                    artifact_dir=str(tmp_path / "pilots"), max_steps=50)
    defaults.update(kw)
    return PilotManifest(**defaults)


def test_register_start_update_stop(tmp_path):
    registry = PilotRegistry(tmp_path / "registry.json")
    manifest = _manifest(tmp_path)
    entry = registry.register_start(manifest)
    assert entry["status"] == "running"
    assert entry["pilot_id"] == manifest.pilot_id
    assert entry["operator"] == "tester"

    registry.register_update(manifest.pilot_id, readiness_status="ready",
                             incident_count=2)
    entry = registry.get_pilot(manifest.pilot_id)
    assert entry["readiness_status"] == "ready"
    assert entry["incident_count"] == 2

    registry.register_stop(manifest.pilot_id, status="completed",
                           final_recommendation="repeat_pilot",
                           report_path="x/pilot_report.md")
    entry = registry.get_pilot(manifest.pilot_id)
    assert entry["status"] == "completed"
    assert entry["ended_at"] is not None
    assert entry["final_recommendation"] == "repeat_pilot"


def test_latest_pilot_works(tmp_path):
    registry = PilotRegistry(tmp_path / "registry.json")
    first = _manifest(tmp_path)
    second = _manifest(tmp_path)
    registry.register_start(first)
    registry.register_start(second)
    assert registry.latest()["pilot_id"] == second.pilot_id
    assert len(registry.list_pilots()) == 2


def test_registry_serializes(tmp_path):
    path = tmp_path / "registry.json"
    registry = PilotRegistry(path)
    manifest = _manifest(tmp_path)
    registry.register_start(manifest)
    data = json.loads(path.read_text())
    assert manifest.pilot_id in data["pilots"]
    # A fresh instance reads the same file.
    assert PilotRegistry(path).get_pilot(manifest.pilot_id) is not None


def test_unknown_pilot_update_raises(tmp_path):
    registry = PilotRegistry(tmp_path / "registry.json")
    with pytest.raises(KeyError):
        registry.register_update("nope", status="running")
    assert registry.latest() is None
    assert registry.get_pilot("nope") is None
