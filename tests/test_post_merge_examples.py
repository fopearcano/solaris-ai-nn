"""Post-merge examples run bounded (no infinite loop) with expected output."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(example, state_dir, timeout=120):
    path = os.path.join(_ROOT, "examples", example)
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", state_dir],
        capture_output=True, text=True, timeout=timeout, cwd=_ROOT)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_assimilation_demo_runs(tmp_path):
    out = _run("run_post_merge_assimilation_demo.py", str(tmp_path / "a"))
    assert "Post-merge assimilation demo" in out
    assert "candidate baseline" in out


def test_baseline_registry_demo_runs(tmp_path):
    out = _run("run_baseline_registry_demo.py", str(tmp_path / "r"))
    assert "Baseline registry demo" in out
    assert "blocked" in out


def test_baseline_comparison_demo_runs(tmp_path):
    out = _run("run_post_merge_baseline_comparison_demo.py", str(tmp_path / "c"))
    assert "baseline comparison demo" in out.lower()
    assert "safety regression dominates" in out.lower()


def test_regression_watch_demo_runs(tmp_path):
    out = _run("run_regression_watch_demo.py", str(tmp_path / "w"))
    assert "Regression watch demo" in out
    assert "rollback" in out.lower()


def test_followup_queue_demo_runs(tmp_path):
    out = _run("run_post_merge_followup_queue_demo.py", str(tmp_path / "f"))
    assert "follow-up queue demo" in out.lower()
    assert "run_mini_soak" in out
