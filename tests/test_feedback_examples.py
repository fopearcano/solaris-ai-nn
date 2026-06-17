"""Feedback examples: all five demos run end to end without an infinite loop."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EX = os.path.join(_ROOT, "examples")


def _run(script, tmp_path):
    proc = subprocess.run(
        [sys.executable, os.path.join(_EX, script),
         "--tester-state-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=_ROOT, timeout=120)
    assert proc.returncode == 0, f"{script}: {proc.stderr}\n{proc.stdout}"
    return proc.stdout


def test_init_demo(tmp_path):
    assert "init demo" in _run("run_tester_feedback_init_demo.py",
                               tmp_path / "init").lower()


def test_ingest_demo(tmp_path):
    assert "ingest demo" in _run("run_tester_feedback_ingest_demo.py",
                                 tmp_path / "ingest").lower()


def test_blocker_demo(tmp_path):
    out = _run("run_tester_feedback_blocker_demo.py", tmp_path / "blocker")
    assert "stop_testing" in out
    assert "release_blocker" in out


def test_bundle_demo(tmp_path):
    out = _run("run_tester_feedback_bundle_demo.py", tmp_path / "bundle")
    assert "local only" in out.lower()


def test_console_demo(tmp_path):
    out = _run("run_tester_feedback_console_demo.py", tmp_path / "console")
    assert "console discovered feedback: true" in out.lower()
