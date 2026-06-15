"""LiveFeederRegistry: loads; missing feeder reported; never starts a feeder."""

from __future__ import annotations

import os

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFeederStatus,
)


def test_registry_loads(tmp_path):
    reg = LiveFeederRegistry(live_root=str(tmp_path))
    path = tmp_path / "rf.jsonl"
    path.write_text('{"modality":"alien_rf","power":0.5,"ts":0}\n')
    reg.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE, output_path=str(path)))
    reg.save()
    loaded = LiveFeederRegistry.load(str(tmp_path))
    assert loaded.get("rf_feed") is not None
    assert loaded.get("rf_feed").output_path == str(path)


def test_missing_feeder_reported(tmp_path):
    reg = LiveFeederRegistry(live_root=str(tmp_path))
    reg.register(LiveFeederDescriptor(
        feeder_id="gone", source_id="g", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE,
        output_path=str(tmp_path / "missing.jsonl")))
    assert reg.missing_feeders()
    assert reg.get("gone").status() == LiveFeederStatus.MISSING


def test_registry_does_not_start_feeder(tmp_path):
    reg = LiveFeederRegistry(live_root=str(tmp_path))
    # The registry has no method to run, launch, or start a feeder.
    assert not hasattr(reg, "start")
    assert not hasattr(reg, "run_feeder")
    assert not hasattr(reg, "launch")


def test_real_world_feeder_requires_governance(tmp_path):
    from solaris_ai_nn.live_field.feeder_contract import LiveFeederMode as M

    reg = LiveFeederRegistry(live_root=str(tmp_path))
    reg.register(LiveFeederDescriptor(
        feeder_id="sensor", source_id="s", modality="alien_thermal",
        mode=M.EXTERNAL_SENSOR_EXPORT, output_path=str(tmp_path / "s.jsonl")))
    assert reg.get("sensor").requires_governance is True
    assert reg.requires_governance() is True
