"""Tester live bundle: created, manifest written, redaction marker, no upload."""

from __future__ import annotations

import json
import os
import sys

from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_live_helpers import approve_governance  # noqa: E402


def _run(tmp_path, approve=False):
    live = str(tmp_path / "live")
    TesterLiveReadOnlyRuntime(
        state_dir=live, tester_state_dir=str(tmp_path / "tester"),
        profile="tester_live_init_only_v0").run()
    if approve:
        approve_governance(live)
    rt = TesterLiveReadOnlyRuntime(
        state_dir=live, tester_state_dir=str(tmp_path / "tester"),
        write_templates=False)
    rt.run()
    return rt


def test_bundle_created(tmp_path):
    rt = _run(tmp_path)
    assert os.path.isdir(rt.bundle.manifest.bundle_dir)
    assert os.path.isfile(os.path.join(
        rt.bundle.manifest.bundle_dir, "README_FOR_LIVE_TESTER.md"))


def test_manifest_written(tmp_path):
    rt = _run(tmp_path)
    manifest_path = os.path.join(rt.bundle.manifest.bundle_dir,
                                 "BUNDLE_MANIFEST.json")
    assert os.path.isfile(manifest_path)
    data = json.load(open(manifest_path))
    assert data["local_only"] is True


def test_privacy_redaction_marker_supported(tmp_path):
    rt = _run(tmp_path, approve=True)
    m = rt.bundle.manifest.to_dict()
    # An approved governance triggers approver-identity redaction in the summary.
    assert "redactions" in m
    summary = json.load(open(os.path.join(
        rt.bundle.manifest.bundle_dir, "GOVERNANCE_SUMMARY.json")))
    assert "approved_by" not in summary


def test_no_upload_publish(tmp_path):
    rt = _run(tmp_path)
    m = rt.bundle.manifest.to_dict()
    assert m["uploaded"] is False
    assert m["published"] is False
    assert m["zipped"] is False
