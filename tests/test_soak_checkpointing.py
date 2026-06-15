"""Soak checkpointing: created, checksum manifest, corruption, break preserved."""

from __future__ import annotations

import os

from solaris_ai_nn.developmental_soak import CheckpointManager


def test_checkpoint_created(tmp_path):
    cm = CheckpointManager(state_dir=str(tmp_path))
    cp = cm.create(tick=0, developmental_life={"composite_growth": 0.3})
    assert cp.checkpoint_id
    assert cm.status()["checkpoint_count"] == 1
    assert os.path.isfile(tmp_path / "soak_checkpoints.jsonl")


def test_checksum_manifest_created(tmp_path):
    cm = CheckpointManager(state_dir=str(tmp_path))
    cp = cm.create(tick=1, module_states={"plural_sensorium": {"x": 1}})
    assert "__all__" in cp.checksum_manifest
    assert cm.verify(cp).ok is True


def test_corrupt_checkpoint_recorded(tmp_path):
    cm = CheckpointManager(state_dir=str(tmp_path))
    cp = cm.create(tick=2)
    cp.checksum_manifest["__all__"] = "tampered"
    result = cm.verify(cp)
    assert result.ok is False
    assert cp.corrupt is True
    assert cm.status()["checkpoint_corruption_count"] == 1
    # The corrupt checkpoint is recorded, not dropped.
    assert cm.status()["checkpoint_count"] == 1


def test_no_auto_delete(tmp_path):
    cm = CheckpointManager(state_dir=str(tmp_path))
    for i in range(3):
        cm.create(tick=i)
    assert cm.status()["checkpoint_count"] == 3
    assert cm.status()["auto_delete"] is False


def test_recovery_preserves_break(tmp_path):
    cm = CheckpointManager(state_dir=str(tmp_path))
    good = cm.create(tick=0)
    bad = cm.create(tick=1)
    bad.checksum_manifest["__all__"] = "tampered"
    cm.verify(bad)
    rec = cm.recover()
    assert rec["recovered"] is True
    assert rec["from_checkpoint"] == good.checkpoint_id
    # The skipped corrupt checkpoint is logged as a continuity break.
    assert rec["break_count"] >= 1
