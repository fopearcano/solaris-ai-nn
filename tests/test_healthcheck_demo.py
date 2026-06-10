"""Tests for the healthcheck demo example."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "run_healthcheck_demo.py"


def test_demo_runs_bounded_and_logs_warning_incident():
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, str(EXAMPLE)],
                          capture_output=True, text=True, timeout=120,
                          cwd=str(REPO))
    assert time.perf_counter() - start < 120
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "clean reading:  level=ok" in out
    assert "simulated stale heartbeat: level=warning" in out
    assert "incidents logged:" in out
    assert "SIMULATED" in out  # the demo is honest about the simulation
