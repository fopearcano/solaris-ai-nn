"""Artifact reader: reads md/json/diff, records corrupt, no modification."""

from __future__ import annotations

import json

from solaris_ai_nn.implementation_intake import ImplementationArtifactReader


def test_markdown_json_diff_artifacts_read(tmp_path):
    reader = ImplementationArtifactReader()
    md = tmp_path / "x.md"
    md.write_text("# title\nbody", encoding="utf-8")
    js = tmp_path / "x.json"
    js.write_text(json.dumps({"a": 1}), encoding="utf-8")
    patch = tmp_path / "x.patch"
    patch.write_text("--- a/x\n+++ b/x\n@@ -1 +1 @@\n+line\n", encoding="utf-8")

    assert reader.read_file("a", str(md)).kind == "markdown"
    assert reader.read_file("b", str(js)).payload == {"a": 1}
    assert reader.read_file("c", str(patch)).kind == "diff"


def test_payload_reading():
    reader = ImplementationArtifactReader()
    assert reader.read_payload("changed", ["src/x.py"]).kind == "list"
    assert reader.read_payload("summary", "text").ok is True
    # Empty payload is flagged.
    res = reader.read_payload("empty", [])
    assert res.ok is False
    assert res.issue.kind == "empty"


def test_corrupt_artifact_recorded(tmp_path):
    reader = ImplementationArtifactReader()
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    res = reader.read_file("bad", str(bad))
    assert res.ok is False
    assert res.issue.kind == "corrupt"
    # The corrupt artifact is preserved as evidence (recorded, not dropped).
    assert any(i.kind == "corrupt" for i in reader.issues)
    assert res.payload == "{not valid json"


def test_missing_file_recorded(tmp_path):
    reader = ImplementationArtifactReader()
    res = reader.read_file("missing", str(tmp_path / "nope.json"))
    assert res.ok is False
    assert res.issue.kind == "missing"


def test_reader_is_read_only(tmp_path):
    reader = ImplementationArtifactReader()
    f = tmp_path / "x.md"
    f.write_text("original", encoding="utf-8")
    reader.read_file("a", str(f))
    assert f.read_text(encoding="utf-8") == "original"
    assert reader.to_dict()["read_only"] is True
