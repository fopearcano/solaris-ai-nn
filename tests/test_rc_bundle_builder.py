"""RC bundle: created, manifest written, missing listed, no private/upload."""

from __future__ import annotations

import os

from _tester_rc_helpers import run_rc, seed_ready_state


def test_bundle_created(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    assert rt.bundle is not None
    assert os.path.isdir(rt.bundle.bundle_dir)


def test_bundle_manifest_written(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    mj = os.path.join(rt.bundle.bundle_dir, "BUNDLE_MANIFEST.json")
    md = os.path.join(rt.bundle.bundle_dir, "BUNDLE_MANIFEST.md")
    assert os.path.isfile(mj)
    assert os.path.isfile(md)


def test_missing_artifacts_listed(tmp_path):
    rt = run_rc(str(tmp_path / "empty"))
    d = rt.bundle.to_dict()
    assert "missing" in d
    assert d["missing_count"] >= 0


def test_no_private_payloads_or_upload(tmp_path):
    rt = run_rc(str(tmp_path / "x"))
    d = rt.bundle.to_dict()
    assert d["includes_private_payloads"] is False
    assert d["uploaded"] is False
    assert d["published"] is False
    assert d["zipped"] is False
