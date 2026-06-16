"""Alpha state layout: directories created, manifest written, reuse, no delete."""

from __future__ import annotations

import os

from solaris_ai_nn.alpha_system import AlphaStateLayout
from solaris_ai_nn.alpha_system.state_layout import SUBDIRECTORIES


def test_state_directories_created(tmp_path):
    layout = AlphaStateLayout(state_root=str(tmp_path / "alpha"))
    layout.initialize()
    for name in SUBDIRECTORIES:
        assert os.path.isdir(os.path.join(str(tmp_path / "alpha"), name))


def test_manifest_written(tmp_path):
    layout = AlphaStateLayout(state_root=str(tmp_path / "alpha"))
    layout.initialize()
    assert os.path.isfile(layout.manifest_path)


def test_existing_directory_reused(tmp_path):
    root = str(tmp_path / "alpha")
    AlphaStateLayout(state_root=root).initialize()
    # A second init reuses the existing directories (created=False).
    layout2 = AlphaStateLayout(state_root=root)
    layout2.initialize()
    assert all(d.existed for d in layout2.directories)


def test_no_deletion_of_existing_state(tmp_path):
    root = str(tmp_path / "alpha")
    layout = AlphaStateLayout(state_root=root)
    layout.initialize()
    # Drop a sentinel file, re-init, and confirm it survives.
    sentinel = os.path.join(root, "runs", "keep_me.txt")
    with open(sentinel, "w", encoding="utf-8") as fh:
        fh.write("keep")
    AlphaStateLayout(state_root=root).initialize()
    assert os.path.isfile(sentinel)
    assert layout.to_dict()["deletes_state"] is False
