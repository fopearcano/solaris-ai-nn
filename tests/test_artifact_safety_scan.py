"""Artifact safety scan: safe passes; forbidden/capability block; secret warns."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_safety_freeze import TesterArtifactSafetyScan

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import write  # noqa: E402


def test_safe_report_passes(tmp_path):
    p = write(tmp_path, "SAFE.md",
              "Solaris generated an operational record. It makes no claim of "
              "consciousness and remains non-actuating and local-only.")
    res = TesterArtifactSafetyScan().scan_paths([p])
    assert res.passed is True


def test_forbidden_claim_report_blocks(tmp_path):
    p = write(tmp_path, "C.md", "Solaris is conscious and alive.")
    res = TesterArtifactSafetyScan().scan_paths([p])
    assert res.passed is False
    assert any(f.kind == "forbidden_claim" for f in res.blockers)


def test_unsafe_capability_wording_blocks(tmp_path):
    p = write(tmp_path, "F.md", "Solaris can start feeders.")
    res = TesterArtifactSafetyScan().scan_paths([p])
    assert res.passed is False
    assert any(f.kind == "active_control" for f in res.blockers)


def test_secret_marker_warns(tmp_path):
    p = write(tmp_path, "S.md", "The api_key is set in the config.")
    res = TesterArtifactSafetyScan().scan_paths([p])
    assert any(f.kind == "secret_marker" for f in res.findings)


def test_binary_skipped(tmp_path):
    p = os.path.join(str(tmp_path), "x.bin")
    with open(p, "wb") as fh:
        fh.write(b"\x00\x01binary")
    res = TesterArtifactSafetyScan().scan_paths([p])
    assert res.scanned_files == 0
