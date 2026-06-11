"""Subprocess tests for the homeostasis examples."""

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


def test_homeostasis_demo_runs(tmp_path):
    out = _run("run_homeostasis_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "dominant need:" in out
    assert "a suggestion, never an act" in out
    assert "claim guard safe: True" in out
    assert (tmp_path / "s" / "need_trace.jsonl").exists()


def test_embodied_homeostasis_demo_runs(tmp_path):
    out = _run("run_embodied_homeostasis_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "dominant need:" in out
    assert "simulation-only" in out
    assert "execute nothing by themselves" in out


def test_need_conflict_demo_runs(tmp_path):
    out = _run("run_need_conflict_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "conflicts resolved:" in out
    assert "BLOCKED" in out
    assert "approach_reward" in out
    assert "surviving suggestion:" in out
    assert "governance_safety > emergency_stop" in out


def test_auto_determination_demo_runs(tmp_path):
    out = _run("run_auto_determination_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "healthy continuity" in out
    assert "safe_shutdown_recommended" in out
    assert "ops supervisor/watchdog decides" in out
    assert "not a metaphysical claim" in out
    # The story holds: being drops, not-being rises across the phases.
    lines = [l for l in out.splitlines()
             if l.startswith(("healthy continuity", "critical incident"))]
    healthy_being = float(lines[0].split()[2])
    troubled_not_being = float(lines[-1].split()[-3])
    assert healthy_being == 1.0
    assert troubled_not_being >= 0.7
