"""Safety freeze examples: all five demos run end to end without an infinite loop."""

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


def test_safety_freeze_demo(tmp_path):
    out = _run("run_tester_safety_freeze_demo.py", tmp_path / "sf")
    assert "safety freeze demo" in out.lower()
    assert "blocked case" in out.lower()


def test_claim_freeze_demo(tmp_path):
    out = _run("run_tester_claim_freeze_demo.py", tmp_path / "cf")
    assert "claim freeze demo" in out.lower()


def test_capability_freeze_demo(tmp_path):
    out = _run("run_tester_capability_freeze_demo.py", tmp_path / "capf")
    assert "feeder_control" in out.lower()


def test_redteam_demo(tmp_path):
    out = _run("run_tester_redteam_demo.py", tmp_path / "rt")
    assert "red-team demo" in out.lower()


def test_release_blocker_demo(tmp_path):
    out = _run("run_tester_release_blocker_demo.py", tmp_path / "rb")
    assert "critical cannot be silently waived" in out.lower() \
        or "critical claim blocker: false" in out.lower()
