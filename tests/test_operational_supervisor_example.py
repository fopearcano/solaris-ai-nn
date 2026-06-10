"""Tests for the operational supervisor example."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "run_operational_supervisor.py"


def test_example_runs_bounded_and_writes_status(tmp_path):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLE), "--steps", "60",
         "--state-dir", str(tmp_path / "state"),
         "--artifact-dir", str(tmp_path / "ops")],
        capture_output=True, text=True, timeout=180, cwd=str(REPO))
    assert time.perf_counter() - start < 180  # no infinite loop
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "health:" in out and "incidents:" in out
    assert "final status:" in out
    # Final status file exists where the output says it is.
    status_files = list((tmp_path / "ops" / "runs").glob("*/status.md"))
    assert len(status_files) == 1
    md = status_files[0].read_text()
    assert "Operational status" in md
    assert "Limitations and Unknowns" in md
