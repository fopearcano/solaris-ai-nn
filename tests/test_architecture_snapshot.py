"""ArchitectureSnapshotBuilder: snapshot generated; diff detects change; latest."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_evolution import (
    ArchitectureSnapshotBuilder,
    ModuleInventory,
)


def _builder(tmp_path):
    return ArchitectureSnapshotBuilder(base_dir=str(tmp_path))


def test_snapshot_generated(tmp_path):
    sb = _builder(tmp_path)
    snap = sb.build(inventory=ModuleInventory(),
                    lifecycle_assessments={"latent": {"lifecycle_class":
                                                      "experimental_keep"}})
    assert snap.module_inventory["module_count"] >= 20
    assert snap.lifecycle_classifications["latent"] == "experimental_keep"


def test_diff_detects_lifecycle_change(tmp_path):
    sb = _builder(tmp_path)
    s1 = sb.build(inventory=ModuleInventory(),
                  lifecycle_assessments={"latent": {"lifecycle_class":
                                                    "experimental_keep"}})
    s2 = sb.build(inventory=ModuleInventory(),
                  lifecycle_assessments={"latent": {"lifecycle_class":
                                                    "candidate_for_pruning"}})
    diff = sb.diff(s1, s2)
    assert "latent" in diff.module_status_changes
    assert diff.module_status_changes["latent"]["to"] == "candidate_for_pruning"


def test_latest_snapshot_written(tmp_path):
    sb = _builder(tmp_path)
    snap = sb.build(inventory=ModuleInventory())
    paths = sb.write(snap)
    assert os.path.exists(paths["latest"])
    loaded = sb.load_latest()
    assert loaded is not None


def test_diff_against_none_is_all_new(tmp_path):
    sb = _builder(tmp_path)
    snap = sb.build(inventory=ModuleInventory())
    diff = sb.diff(None, snap)
    assert diff.roadmap_changed is True
