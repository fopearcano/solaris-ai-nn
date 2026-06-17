"""Tester fixture examples: all five demos run end to end without an infinite loop."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EX = os.path.join(_ROOT, "examples")


def _run(script, state_dir):
    proc = subprocess.run(
        [sys.executable, os.path.join(_EX, script), "--state-dir", state_dir],
        capture_output=True, text=True, cwd=_ROOT, timeout=120)
    assert proc.returncode == 0, f"{script}: {proc.stderr}\n{proc.stdout}"
    return proc.stdout


def test_fixture_demo(tmp_path):
    out = _run("run_tester_fixture_demo.py", str(tmp_path / "demo"))
    assert "tester fixture demo" in out.lower()


def test_golden_demo(tmp_path):
    out = _run("run_tester_golden_demo.py", str(tmp_path / "golden"))
    assert "golden manifest" in out.lower()


def test_reproducibility_demo(tmp_path):
    out = _run("run_tester_reproducibility_demo.py", str(tmp_path / "repro"))
    assert "reproducibility" in out.lower()
    assert "fail" in out.lower()  # demonstrates the missing-required fail case


def test_regression_demo(tmp_path):
    out = _run("run_tester_regression_demo.py", str(tmp_path / "regr"))
    assert "regression" in out.lower()
    assert "membrane disappeared" in out.lower()


def test_bundle_demo(tmp_path):
    out = _run("run_tester_bundle_demo.py", str(tmp_path / "bundle"))
    assert "bundle" in out.lower()
    assert "missing optional" in out.lower()
