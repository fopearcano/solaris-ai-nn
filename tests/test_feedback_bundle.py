"""Feedback bundle: created, manifest written, redaction marker, no upload."""

from __future__ import annotations

import json
import os
import sys

from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_feedback_helpers import ingest, sample_path  # noqa: E402


def _bundle(tmp_path):
    tester = str(tmp_path / "t")
    ingest(tester, sample_path("sample_bug_report.json"))
    rt = TesterFeedbackRuntime(tester_state_dir=tester, build_bundle=True)
    rt.run()
    return rt


def test_bundle_created(tmp_path):
    rt = _bundle(tmp_path)
    assert os.path.isdir(rt.bundle.manifest.bundle_dir)
    assert os.path.isfile(os.path.join(rt.bundle.manifest.bundle_dir,
                                       "README_FOR_DEVELOPER.md"))


def test_manifest_written(tmp_path):
    rt = _bundle(tmp_path)
    manifest = os.path.join(rt.bundle.manifest.bundle_dir,
                            "BUNDLE_MANIFEST.json")
    assert os.path.isfile(manifest)
    data = json.load(open(manifest))
    assert data["local_only"] is True


def test_privacy_redaction_marker_supported(tmp_path):
    rt = _bundle(tmp_path)
    m = rt.bundle.manifest.to_dict()
    assert "redaction_count" in m
    assert "privacy_warning" in m


def test_no_upload_publish(tmp_path):
    rt = _bundle(tmp_path)
    m = rt.bundle.manifest.to_dict()
    assert m["uploaded"] is False
    assert m["published"] is False
    assert m["includes_private_payloads"] is False
