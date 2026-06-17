"""Tester live examples: all five demos run end to end without an infinite loop."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EX = os.path.join(_ROOT, "examples")


def _run(script, tmp_path, name):
    proc = subprocess.run(
        [sys.executable, os.path.join(_EX, script),
         "--state-dir", os.path.join(str(tmp_path), name, "live"),
         "--tester-state-dir", os.path.join(str(tmp_path), name, "tester")],
        capture_output=True, text=True, cwd=_ROOT, timeout=120)
    assert proc.returncode == 0, f"{script}: {proc.stderr}\n{proc.stdout}"
    return proc.stdout


def test_init_demo(tmp_path):
    out = _run("run_tester_live_init_demo.py", tmp_path, "init")
    assert "tester live init demo" in out.lower()


def test_doctor_demo(tmp_path):
    out = _run("run_tester_live_doctor_demo.py", tmp_path, "doctor")
    assert "doctor" in out.lower()
    assert "blocked" in out.lower()


def test_samples_demo(tmp_path):
    out = _run("run_tester_live_samples_demo.py", tmp_path, "samples")
    assert "safe accepted" in out.lower()


def test_run_demo(tmp_path):
    out = _run("run_tester_live_run_demo.py", tmp_path, "run")
    assert "membrane impressions" in out.lower()


def test_bundle_demo(tmp_path):
    out = _run("run_tester_live_bundle_demo.py", tmp_path, "bundle")
    assert "bundle" in out.lower()
    assert "local only" in out.lower()
