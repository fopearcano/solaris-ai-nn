"""Subprocess tests for the ego examples."""

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


def test_ego_boundary_demo_runs(tmp_path):
    out = _run("run_ego_boundary_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "operational, not" in out
    assert "Ego boundary registry" in out
    assert "claim guard safe: True" in out
    assert "claims no consciousness" in out
    assert (tmp_path / "s" / "self_report.md").exists()
    assert (tmp_path / "s" / "narrative_trace.jsonl").exists()
    assert (tmp_path / "s" / "ego_boundaries.json").exists()


def test_dimensional_comparison_demo_runs(tmp_path):
    out = _run("run_dimensional_comparison_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "frames (six axes each):" in out
    assert "observed stream event" in out
    assert "sidecar suggestion" in out
    assert "distance=" in out
    assert "not" in out and "experiential" in out


def test_identity_continuity_demo_runs(tmp_path):
    out = _run("run_identity_continuity_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "clean start" in out
    assert "checkpoint restore" in out
    assert "restart gap" in out
    assert "mismatched anchor" in out
    assert "runtime continuity gap" in out or "mismatch" in out
    assert "not personhood" in out


def test_counterfactual_boundary_demo_runs(tmp_path):
    out = _run("run_counterfactual_boundary_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "evidence status: counterfactual" in out
    assert "blocked: True" in out
    assert "nothing was treated as real" in out


def test_self_report_demo_runs(tmp_path):
    out = _run("run_self_report_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "claim guard safe: True" in out
    assert "Q: what is the self-model summary?" in out
    assert "identity-claim scan would block" in out
    assert (tmp_path / "s" / "self_report.md").exists()
