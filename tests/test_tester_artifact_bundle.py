"""Tester artifact bundle: created, manifest written, missing optional, no upload."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_fixture_spine import TesterBundleBuilder


def test_bundle_created(tmp_path):
    bundle = TesterBundleBuilder().build(
        state_dir=str(tmp_path), run_id="r1",
        run_summary={"tester_run_id": "r1"},
        artifacts={"tester_report": None}, optional_artifacts={})
    assert os.path.isdir(bundle.manifest.bundle_dir)
    assert os.path.isfile(os.path.join(bundle.manifest.bundle_dir,
                                       "README_FOR_TESTER.md"))
    assert os.path.isfile(bundle.feedback_form_path)


def test_manifest_written(tmp_path):
    TesterBundleBuilder().build(
        state_dir=str(tmp_path), run_id="r2",
        run_summary={"tester_run_id": "r2"}, artifacts={}, optional_artifacts={})
    manifest_path = os.path.join(str(tmp_path), "bundles", "TESTER_BUNDLE_r2",
                                 "BUNDLE_MANIFEST.json")
    assert os.path.isfile(manifest_path)
    data = json.load(open(manifest_path))
    assert data["local_only"] is True


def test_missing_optional_artifacts_listed(tmp_path):
    bundle = TesterBundleBuilder().build(
        state_dir=str(tmp_path), run_id="r3",
        run_summary={}, artifacts={},
        optional_artifacts={"ontogenesis_summary": None,
                            "cognition_summary": None})
    assert "ontogenesis_summary" in bundle.manifest.missing_optional
    assert "cognition_summary" in bundle.manifest.missing_optional


def test_no_upload_or_publish(tmp_path):
    bundle = TesterBundleBuilder().build(
        state_dir=str(tmp_path), run_id="r4", run_summary={}, artifacts={},
        optional_artifacts={})
    d = bundle.manifest.to_dict()
    assert d["uploaded"] is False
    assert d["published"] is False
    assert d["zipped"] is False


def test_copies_real_artifact(tmp_path):
    src = tmp_path / "report.md"
    src.write_text("# report")
    bundle = TesterBundleBuilder().build(
        state_dir=str(tmp_path), run_id="r5", run_summary={},
        artifacts={"tester_report": str(src)}, optional_artifacts={})
    copied = [e for e in bundle.manifest.entries if e.get("kind") == "copy"]
    assert any("report" in e["name"] for e in copied)
