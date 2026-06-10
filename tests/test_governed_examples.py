"""Subprocess tests for the governance examples."""

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
    assert time.perf_counter() - start < timeout, f"{script} too slow"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_governed_bounded_example_runs(tmp_path):
    out = _run("run_governed_bounded_experiment.py",
               "--steps", "60",
               "--state-dir", str(tmp_path / "state"),
               "--artifact-dir", str(tmp_path / "ops"),
               "--governance-dir", str(tmp_path / "gov"))
    assert "policy status:    allowed" in out
    assert "risk level:       low" in out
    assert "claim guard:      safe" in out
    assert (tmp_path / "gov" / "post_run_review.json").exists()


def test_governed_plasticity_example_runs(tmp_path):
    out = _run("run_governed_plasticity_request.py",
               "--governance-dir", str(tmp_path / "gov"))
    assert "Act 1: active mutation WITHOUT approval" in out
    assert "rejected" in out
    assert "Act 3: the same mutation WITH approval" in out
    assert "applied: True" in out


def test_emergency_stop_demo_runs(tmp_path):
    out = _run("run_emergency_stop_demo.py",
               "--state-dir", str(tmp_path / "state"),
               "--artifact-dir", str(tmp_path / "ops"),
               "--governance-dir", str(tmp_path / "gov"))
    assert "emergency requested: True" in out
    assert "shutdown graceful:   True" in out
    assert "emergency_stop" in out


def test_runbook_generation_works(tmp_path):
    out = _run("generate_runbook.py", "--type", "plasticity",
               "--output-dir", str(tmp_path / "rb"))
    assert "runbook type: plasticity" in out
    assert (tmp_path / "rb" / "runbook_plasticity.md").exists()
    md = (tmp_path / "rb" / "runbook_plasticity.md").read_text()
    assert "Rollback procedure" in md


def test_claim_guard_demo_works():
    out = _run("run_claim_guard_demo.py", timeout=60)
    assert "unsafe sample" in out
    assert "safe: False" in out
    assert "safe: True" in out  # the safe sample
    assert "consciousness-inspired" in out
