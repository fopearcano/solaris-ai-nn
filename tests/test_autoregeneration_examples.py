"""Subprocess tests for the auto-regeneration examples."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def _run(script, *args, timeout=180):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
    assert time.perf_counter() - start < timeout, f"{script}: no infinite loop"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_diagnostics_demo_runs(tmp_path):
    out = _run("run_autoregeneration_diagnostics_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "detect, not" in out
    assert "degradation signals:" in out
    assert "claim guard safe: True" in out
    assert "never source code" in out


def test_state_hygiene_demo_runs(tmp_path):
    out = _run("run_state_hygiene_demo.py", "--state-dir", str(tmp_path / "s"))
    assert "archive/quarantine, never delete" in out
    assert "quarantined ->" in out
    assert (tmp_path / "s" / "quarantine").exists()


def test_symbol_hygiene_demo_runs(tmp_path):
    out = _run("run_symbol_hygiene_demo.py", "--state-dir", str(tmp_path / "s"))
    assert "mark/merge, never rename" in out
    assert "proposed hygiene actions:" in out
    assert "claim guard safe: True" in out


def test_world_model_hygiene_demo_runs(tmp_path):
    out = _run("run_world_model_hygiene_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "mark/weaken, keep evidence" in out
    assert "hypothesis test requests:" in out
    assert "claim guard safe: True" in out


def test_drift_recovery_demo_runs(tmp_path):
    out = _run("run_drift_recovery_demo.py", "--state-dir", str(tmp_path / "s"))
    assert "stabilize runaway" in out
    assert "runaway drift" in out
    assert "claim guard safe: True" in out


def test_safety_demo_runs(tmp_path):
    out = _run("run_autoregeneration_safety_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "not a back door" in out
    assert "source-code repair blocked:      True" in out
    assert "evidence deletion blocked:       True" in out
    assert "claim guard safe: True" in out
