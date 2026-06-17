"""Live observation examples run end to end without hanging."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(script, tmp_path, extra=None):
    path = os.path.join(_ROOT, "examples", script)
    cmd = [sys.executable, path, "--state-dir", str(tmp_path)]
    cmd += extra or []
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_observation_demo_runs(tmp_path):
    out = _run("run_live_observation_demo.py", tmp_path)
    assert "Post-birth live observation demo" in out
    assert "learns / starts feed: False / False" in out


def test_source_health_demo_runs(tmp_path):
    out = _run("run_live_source_health_demo.py", tmp_path)
    assert "Live source-health demo" in out
    assert "live sources" in out


def test_source_diet_demo_runs(tmp_path):
    out = _run("run_live_source_diet_demo.py", tmp_path)
    assert "Live source-diet demo" in out
    assert "balance" in out


def test_metabolism_calibration_demo_runs(tmp_path):
    out = _run("run_live_metabolism_calibration_demo.py", tmp_path)
    assert "metabolism calibration demo (report-only)" in out.lower()
    assert "applied=False" in out


def test_stability_gate_demo_runs(tmp_path):
    out = _run("run_live_stability_gate_demo.py", tmp_path)
    assert "stability-gate demo" in out.lower()


def test_stability_gate_overload_blocks(tmp_path):
    out = _run("run_live_stability_gate_demo.py", tmp_path,
               ["--fixture", "sample_overload_events.jsonl"])
    assert "blocked_by_overload" in out
