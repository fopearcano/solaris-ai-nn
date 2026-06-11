"""Subprocess tests for the executive examples."""

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


def test_executive_demo_runs(tmp_path):
    out = _run("run_executive_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "arbitration, not agency" in out
    assert "selected suggestion:" in out
    assert "claim guard safe: True" in out
    assert (tmp_path / "s" / "decision_trace.jsonl").exists()
    assert (tmp_path / "s" / "executive_report.md").exists()


def test_embodied_executive_demo_runs(tmp_path):
    out = _run("run_embodied_executive_demo.py", "--steps", "150",
               "--state-dir", str(tmp_path / "s"))
    assert "simulation-only" in out
    assert "executed simulated actions:" in out
    assert "selections execute only inside the GridWorld simulation" in out


def test_executive_inhibition_demo_runs(tmp_path):
    out = _run("run_executive_inhibition_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "inhibition table:" in out
    assert "selected:" in out
    assert "every blocked candidate stays on the record" in out


def test_short_plan_demo_runs(tmp_path):
    out = _run("run_short_plan_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "suggestion-only" in out
    assert "selected plan:" in out
    assert "7-step plan refused: True" in out
    assert "long-horizon autonomous planning is refused" in out


def test_executive_emergency_demo_runs(tmp_path):
    out = _run("run_executive_emergency_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "phase 2 (critical):  mode=emergency" in out
    assert "can leave emergency while it holds: False" in out
    assert "only ops/governance clearing the condition" in out
