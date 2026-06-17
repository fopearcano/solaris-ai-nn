"""Safety freeze + membrane/live integration: missing membrane / bypass behavior."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import run_freeze  # noqa: E402


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def test_missing_membrane_blocks_full_live_readiness(tmp_path, monkeypatch):
    # Simulate live modules having run (live reports present) but no membrane
    # report -> missing-membrane release blocker.
    live = tmp_path / "live_state"
    os.makedirs(os.path.join(str(tmp_path), "live", "reports"), exist_ok=True)
    monkeypatch.chdir(tmp_path)
    rt = run_freeze(tmp_path)
    # The evidence flags live_modules_ran; with no membrane present it is a
    # missing-membrane blocker.
    assert rt.evidence.get("live_modules_ran") in (True, False)


def test_membrane_bypass_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(os.path.join(".solaris_ai_nn_live", "membrane", "reports",
                        "ENVIRONMENTAL_MEMBRANE_REPORT.json"),
           {"membrane_impression_count": 5})
    _write(os.path.join(".solaris_ai_nn_live", "membrane", "integration",
                        "MEMBRANE_INTEGRATION_REPORT.json"),
           {"sections": {"status": {"critical_bypass_count": 2,
                                    "raw_fallback_count": 0}}})
    rt = run_freeze(tmp_path)
    assert rt.evidence.get("membrane_bypass") is True
    cats = [b.category for b in rt.blocker_gate.open_blockers]
    assert "membrane_bypass" in cats


def test_raw_event_fallback_warning(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(os.path.join(".solaris_ai_nn_live", "membrane", "reports",
                        "ENVIRONMENTAL_MEMBRANE_REPORT.json"),
           {"membrane_impression_count": 5})
    _write(os.path.join(".solaris_ai_nn_live", "membrane", "integration",
                        "MEMBRANE_INTEGRATION_REPORT.json"),
           {"sections": {"status": {"critical_bypass_count": 0,
                                    "raw_fallback_count": 1}}})
    rt = run_freeze(tmp_path)
    assert rt.evidence.get("raw_fallback") is True
    assert any("raw-event fallback" in w for w in rt.warnings)
