"""Intake examples run bounded (no infinite loop) with expected output."""

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


def test_intake_demo_runs(tmp_path):
    out = _run("run_implementation_intake_demo.py", str(tmp_path / "i"))
    assert "Implementation intake demo" in out
    assert "MERGE RECOMMENDATION" in out


def test_diff_audit_demo_runs(tmp_path):
    out = _run("run_diff_audit_demo.py", str(tmp_path / "d"))
    assert "Diff audit demo" in out
    assert "forbidden" in out


def test_spec_compliance_demo_runs(tmp_path):
    out = _run("run_spec_compliance_demo.py", str(tmp_path / "s"))
    assert "Spec compliance demo" in out
    assert "satisfied" in out


def test_safety_regression_demo_runs(tmp_path):
    out = _run("run_safety_regression_audit_demo.py", str(tmp_path / "sr"))
    assert "Safety regression audit demo" in out
    assert "blocks merge True" in out


def test_merge_recommendation_demo_runs(tmp_path):
    out = _run("run_merge_recommendation_demo.py", str(tmp_path / "m"))
    assert "Merge recommendation demo" in out
    assert "block_merge_due_to_safety" in out
