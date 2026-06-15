"""Soak examples run bounded (no infinite loop) and produce expected output."""

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


def test_preflight_demo_runs(tmp_path):
    out = _run("run_soak_preflight_demo.py", str(tmp_path / "pf"))
    assert "Soak preflight demo" in out
    assert "never starts the run" in out


def test_short_soak_demo_runs(tmp_path):
    out = _run("run_developmental_soak_short_demo.py", str(tmp_path / "ss"))
    assert "Developmental soak short demo" in out
    assert "checkpoints" in out


def test_weekly_review_demo_runs(tmp_path):
    out = _run("run_weekly_review_demo.py", str(tmp_path / "wr"))
    assert "Weekly review demo" in out
    assert "decision" in out


def test_control_arms_demo_runs(tmp_path):
    out = _run("run_soak_control_arms_demo.py", str(tmp_path / "ca"))
    assert "Soak control arms demo" in out
    assert "full_stack" in out


def test_post_run_autopsy_demo_runs(tmp_path):
    out = _run("run_post_run_autopsy_demo.py", str(tmp_path / "ap"))
    assert "Post-run autopsy demo" in out
    assert "recommendation" in out
