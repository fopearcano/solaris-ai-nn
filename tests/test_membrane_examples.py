"""Environmental membrane examples run end to end without hanging."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(script, tmp_path, extra=None):
    path = os.path.join(_ROOT, "examples", script)
    cmd = [sys.executable, path, "--state-dir", str(tmp_path)]
    cmd += extra or []
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_environmental_membrane_demo_runs(tmp_path):
    out = _run("run_environmental_membrane_demo.py", tmp_path)
    assert "Environmental membrane demo" in out
    assert "starts feeders/net  : False / False" in out


def test_receptor_field_demo_runs(tmp_path):
    out = _run("run_receptor_field_demo.py", tmp_path)
    assert "Receptor field demo" in out
    assert "unknown_source_receptor" in out


def test_permeability_demo_runs(tmp_path):
    out = _run("run_permeability_demo.py", tmp_path)
    assert "Permeability demo" in out
    assert "quarantine" in out


def test_source_pressure_demo_runs(tmp_path):
    out = _run("run_source_pressure_demo.py", tmp_path)
    assert "Source pressure demo" in out
    assert "operator_dominated" in out


def test_membrane_memory_demo_runs(tmp_path):
    out = _run("run_membrane_memory_demo.py", tmp_path)
    assert "Membrane memory demo" in out
    assert "toxicity" in out
