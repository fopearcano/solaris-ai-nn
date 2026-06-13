"""Subprocess tests for the developmental nursery / ecology examples."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def _run(script, *args, timeout=300):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
    assert time.perf_counter() - start < timeout, f"{script}: no infinite loop"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_developmental_nursery_demo_runs(tmp_path):
    out = _run("run_developmental_nursery_demo.py", "--steps", "200",
               "--state-dir", str(tmp_path / "s"))
    assert "a world, not a teacher" in out
    assert "ecology events:" in out
    assert "claim guard safe: True" in out
    assert "no teacher, no LLM, no real-world action" in out
    assert (tmp_path / "s" / "ecology_report.md").exists()


def test_deprivation_nursery_demo_runs(tmp_path):
    out = _run("run_deprivation_nursery_demo.py", "--steps", "200",
               "--state-dir", str(tmp_path / "s"))
    assert "scarcity, silence, recovery" in out
    assert "silent steps:" in out
    assert "claim guard safe: True" in out
    assert (tmp_path / "s" / "ecology_report.md").exists()


def test_delayed_consequence_demo_runs(tmp_path):
    out = _run("run_delayed_consequence_demo.py", "--steps", "200",
               "--state-dir", str(tmp_path / "s"))
    assert "cause now, effect later" in out
    assert "delayed groups made:" in out
    assert "never a label" in out
    assert (tmp_path / "s" / "ecology_report.md").exists()


def test_seasonal_shift_demo_runs(tmp_path):
    out = _run("run_seasonal_shift_demo.py", "--steps", "300",
               "--state-dir", str(tmp_path / "s"))
    assert "slow change is life" in out
    assert "seasonal shifts:" in out
    assert "season timeline" in out
    assert (tmp_path / "s" / "ecology_report.md").exists()


def test_anomaly_nursery_demo_runs(tmp_path):
    out = _run("run_anomaly_nursery_demo.py", "--steps", "200",
               "--state-dir", str(tmp_path / "s"))
    assert "perturbations, never errors" in out
    assert "anomalies generated:" in out
    assert "is_error=False" in out
    assert (tmp_path / "s" / "ecology_report.md").exists()
