"""Console examples: all five demos run end to end without an infinite loop."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EX = os.path.join(_ROOT, "examples")


def _run(script, *args):
    proc = subprocess.run([sys.executable, os.path.join(_EX, script), *args],
                          capture_output=True, text=True, cwd=_ROOT, timeout=120)
    assert proc.returncode == 0, f"{script}: {proc.stderr}\n{proc.stdout}"
    return proc.stdout


def test_console_demo(tmp_path):
    out = _run("run_tester_console_demo.py",
               "--state-dir", str(tmp_path / "live"),
               "--tester-state-dir", str(tmp_path / "tester"),
               "--console-dir", str(tmp_path / "console"))
    assert "tester console demo" in out.lower()


def test_status_demo(tmp_path):
    out = _run("run_tester_console_status_demo.py",
               "--tester-state-dir", str(tmp_path / "status"))
    assert "status demo" in out.lower()
    assert "blocked" in out.lower()


def test_safety_demo(tmp_path):
    out = _run("run_tester_console_safety_demo.py",
               "--tester-state-dir", str(tmp_path / "safety"))
    assert "membrane_bypass" in out.lower()
    assert "fix safety blocker" in out.lower()


def test_runs_demo(tmp_path):
    out = _run("run_tester_console_runs_demo.py",
               "--tester-state-dir", str(tmp_path / "runs"))
    assert "latest" in out.lower()


def test_next_actions_demo(tmp_path):
    out = _run("run_tester_console_next_actions_demo.py",
               "--tester-state-dir", str(tmp_path / "next"))
    assert "fix safety blocker" in out.lower()
