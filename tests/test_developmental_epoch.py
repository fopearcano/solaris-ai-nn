"""DevelopmentalEpoch: serializes; boundary explainable; survives restart."""

from __future__ import annotations

import os

from solaris_ai_nn.developmental_life import (
    DevelopmentalEpoch,
    DevelopmentalMemoryStore,
    EpochBoundary,
    EpochTransitionReason,
)


def test_epoch_serializes():
    epoch = DevelopmentalEpoch(
        epoch_index=0, start_tick=0,
        open_boundary=EpochBoundary(EpochTransitionReason.TIME_ELAPSED))
    d = epoch.to_dict()
    assert d["epoch_index"] == 0
    assert d["closed"] is False
    assert "not a biological age" in d["note"]


def test_boundary_explainable():
    epoch = DevelopmentalEpoch(epoch_index=1, start_tick=3)
    epoch.close(6, EpochBoundary(EpochTransitionReason.PLATEAU_DETECTED,
                                 detail="composite flat",
                                 evidence_refs=["growth_state"]))
    assert epoch.closed is True
    assert epoch.close_boundary.reason == EpochTransitionReason.PLATEAU_DETECTED
    assert epoch.close_boundary.evidence_refs == ["growth_state"]


def test_survives_restart(tmp_path):
    store = DevelopmentalMemoryStore(state_dir=str(tmp_path))
    epoch = DevelopmentalEpoch(epoch_index=0, start_tick=0)
    store.record_epoch(epoch.to_dict())
    store.write_index()
    # A fresh store reloads the persisted epoch index (survives restart).
    reloaded = DevelopmentalMemoryStore(state_dir=str(tmp_path))
    reloaded.load_index()
    assert reloaded.index.to_dict()["epoch_count"] == 1
    assert os.path.isfile(tmp_path / "epochs.jsonl")
