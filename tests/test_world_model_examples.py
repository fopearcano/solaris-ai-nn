"""Subprocess tests for the world-model examples."""

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


def test_world_model_demo_runs(tmp_path):
    out = _run("run_world_model_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "graph nodes:" in out
    assert "strongest assoc.:" in out
    assert "A: The world model holds" in out
    assert (tmp_path / "s" / "world_model.json").exists()


def test_embodied_world_model_demo_runs(tmp_path):
    out = _run("run_embodied_world_model_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "observed objects:" in out
    assert "claim guard safe: True" in out
    assert (tmp_path / "s" / "world_model_report.md").exists()


def test_prediction_demo_runs(tmp_path):
    out = _run("run_world_model_prediction_demo.py", "--steps", "150",
               "--state-dir", str(tmp_path / "s"))
    assert "phase 1 (predictable):" in out
    assert "phase 2 (changed):" in out
    assert "never execute actions" in out
    # The story holds: phase 1 hits more than phase 2.
    phase1 = int(out.split("phase 1 (predictable): ")[1].split("/")[0])
    phase2 = int(out.split("phase 2 (changed):     ")[1].split("/")[0])
    assert phase1 > phase2


def test_pruning_demo_runs(tmp_path):
    out = _run("run_world_model_pruning_demo.py", "--dry-run",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "dry run:          True" in out
    assert "unchanged: True" in out
    assert "evidence summaries were preserved" in out
    assert "requires governance approval" in out
