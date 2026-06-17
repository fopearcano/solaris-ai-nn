"""Live cognition examples run end to end without hanging."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(script, tmp_path, extra=None):
    path = os.path.join(_ROOT, "examples", script)
    cmd = [sys.executable, path, "--state-dir", str(tmp_path)]
    cmd += extra or []
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_cognition_demo_runs(tmp_path):
    out = _run("run_live_cognition_demo.py", tmp_path)
    assert "First live cognition demo" in out
    assert "enables action / signs=lang / traces=reasoning : False" in out


def test_anticipation_demo_runs(tmp_path):
    out = _run("run_live_anticipation_demo.py", tmp_path)
    assert "Live anticipation demo" in out
    assert "anticipations" in out


def test_uncertainty_demo_runs(tmp_path):
    out = _run("run_live_uncertainty_demo.py", tmp_path)
    assert "Live uncertainty demo" in out
    assert "contradiction raises it : True" in out


def test_internal_simulation_demo_runs(tmp_path):
    out = _run("run_live_internal_simulation_demo.py", tmp_path)
    assert "Live internal simulation demo" in out
    assert "controls_feeders=False" in out


def test_cognition_gate_demo_runs(tmp_path):
    out = _run("run_live_cognition_gate_demo.py", tmp_path)
    assert "Live cognition gate demo" in out
    assert "weak-signs scenario" in out
