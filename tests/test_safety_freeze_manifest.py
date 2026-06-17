"""Safety freeze manifest: generated, readiness computed, blocker counts."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import run_freeze  # noqa: E402
from solaris_ai_nn.tester_safety_freeze import SafetyFreezeStatus  # noqa: E402


def test_manifest_generated(tmp_path):
    rt = run_freeze(tmp_path)
    assert rt.manifest is not None
    d = rt.manifest.to_dict()
    assert d["report_gate_only"] is True
    manifest_path = os.path.join(
        str(tmp_path), "safety_freeze", "manifests",
        "TESTER_SAFETY_FREEZE_MANIFEST.json")
    assert os.path.isfile(manifest_path)


def test_readiness_status_computed(tmp_path):
    rt = run_freeze(tmp_path)
    assert rt.manifest.readiness in SafetyFreezeStatus.ALL


def test_blocker_counts_included(tmp_path):
    rt = run_freeze(tmp_path)
    d = rt.manifest.to_dict()
    assert "release_blocker_count" in d
    assert "forbidden_claim_count" in d
    assert "critical_open_count" in d
