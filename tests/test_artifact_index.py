"""ArtifactIndexer: index generated; checksums; large file not loaded fully."""

from __future__ import annotations

import os

from solaris_ai_nn.operator_console import ArtifactIndexer
from solaris_ai_nn.operator_console.artifact_index import LARGE_FILE_BYTES


def test_index_generated(tmp_path):
    base = str(tmp_path / "state")
    os.makedirs(base)
    with open(os.path.join(base, "a.json"), "w", encoding="utf-8") as fh:
        fh.write('{"x": 1}')
    index = ArtifactIndexer([base]).index()
    assert index.to_dict()["artifact_count"] == 1
    assert index.records[0].artifact_type == "json"


def test_checksum_computed(tmp_path):
    base = str(tmp_path / "state")
    os.makedirs(base)
    with open(os.path.join(base, "a.txt"), "w", encoding="utf-8") as fh:
        fh.write("hello")
    index = ArtifactIndexer([base]).index()
    rec = index.records[0]
    assert rec.checksum and len(rec.checksum) == 64  # sha256 hex
    assert rec.readable and not rec.corrupted


def test_large_file_indexed_not_loaded_fully(tmp_path):
    base = str(tmp_path / "state")
    os.makedirs(base)
    big = os.path.join(base, "big.jsonl")
    with open(big, "w", encoding="utf-8") as fh:
        fh.write("x" * (LARGE_FILE_BYTES + 10))
    index = ArtifactIndexer([base]).index()
    rec = next(r for r in index.records if r.path.endswith("big.jsonl"))
    # The large file is indexed (metadata + streamed checksum) and flagged
    # large; it is never read fully into memory.
    assert rec.large is True
    assert rec.size > LARGE_FILE_BYTES
    assert rec.checksum is not None


def test_safety_relevance_flagged(tmp_path):
    base = str(tmp_path / "state")
    os.makedirs(base)
    with open(os.path.join(base, "SAFETY_INVARIANT_REPORT.json"), "w",
              encoding="utf-8") as fh:
        fh.write("{}")
    index = ArtifactIndexer([base]).index()
    assert index.records[0].safety_relevance is True


def test_corrupted_artifact_not_hidden(tmp_path):
    base = str(tmp_path / "state")
    os.makedirs(base)
    os.symlink(os.path.join(base, "missing.json"),
               os.path.join(base, "dangling.json"))
    index = ArtifactIndexer([base]).index()
    assert index.to_dict()["corrupted_count"] >= 1
