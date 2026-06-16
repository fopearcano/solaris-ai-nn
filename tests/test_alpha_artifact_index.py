"""Alpha artifact index: artifacts indexed, missing markers, no deletion."""

from __future__ import annotations

import os

from solaris_ai_nn.alpha_system import AlphaArtifactIndex, AlphaArtifactKind


def test_artifacts_indexed(tmp_path):
    idx = AlphaArtifactIndex(state_root=str(tmp_path), run_id="run_1")
    idx.add(AlphaArtifactKind.ALPHA_REPORT, ref="report.md")
    idx.add(AlphaArtifactKind.STATE_MANIFEST, ref="manifest.json")
    assert idx.index()["alpha_artifact_count"] == 2
    assert idx.index()["present_artifact_count"] == 2


def test_missing_markers_indexed(tmp_path):
    idx = AlphaArtifactIndex(state_root=str(tmp_path), run_id="run_1")
    idx.add_missing("soak_dossier")
    idx.add_skipped_module("live_field")
    assert idx.index()["missing_artifact_count"] == 2
    kinds = {r.kind for r in idx.records}
    assert AlphaArtifactKind.MISSING_ARTIFACT_MARKER in kinds
    assert AlphaArtifactKind.SKIPPED_MODULE_MARKER in kinds


def test_run_id_assigned():
    idx = AlphaArtifactIndex(state_root="/tmp/x")
    assert idx.run_id.startswith("alpha_run_")


def test_stale_artifacts_not_deleted(tmp_path):
    idx = AlphaArtifactIndex(state_root=str(tmp_path), run_id="run_1")
    idx.add(AlphaArtifactKind.ALPHA_REPORT, ref="report.md")
    paths = idx.write()
    assert os.path.isfile(paths["json"])
    assert idx.to_dict()["deletes_stale_artifacts"] is False
    # Writing a second index does not remove a pre-existing unrelated file.
    sentinel = os.path.join(str(tmp_path), "index", "old.txt")
    with open(sentinel, "w", encoding="utf-8") as fh:
        fh.write("old")
    AlphaArtifactIndex(state_root=str(tmp_path), run_id="run_2").write()
    assert os.path.isfile(sentinel)
