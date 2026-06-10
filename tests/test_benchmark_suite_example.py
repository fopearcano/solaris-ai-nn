"""Tests for the benchmark suite example CLI."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "run_benchmark_suite.py"


def test_quick_suite_runs_bounded(tmp_path):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLE), "--quick", "--steps", "50",
         "--output-dir", str(tmp_path / "bench")],
        capture_output=True, text=True, timeout=300, cwd=str(REPO),
    )
    assert time.perf_counter() - start < 300  # no infinite loop
    assert proc.returncode == 0, proc.stderr
    assert "benchmark suite" in proc.stdout
    assert "no consciousness score" in proc.stdout
    # Summary files created.
    assert (tmp_path / "bench" / "suite_summary.json").exists()
    assert (tmp_path / "bench" / "suite_summary.md").exists()
    runs = list((tmp_path / "bench" / "runs").glob("*/result.json"))
    assert len(runs) == 4  # the quick suite
