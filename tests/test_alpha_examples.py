"""Alpha examples run end to end without hanging."""

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


def test_alpha_e2e_demo_runs(tmp_path):
    out = _run("run_alpha_e2e_demo.py", tmp_path, ["--max-ticks", "25"])
    assert "Alpha end-to-end demo" in out
    assert "controls feeders/git  : False / False" in out


def test_alpha_doctor_demo_runs(tmp_path):
    out = _run("run_alpha_doctor_demo.py", tmp_path)
    assert "Alpha doctor demo" in out


def test_alpha_module_registry_demo_runs(tmp_path):
    out = _run("run_alpha_module_registry_demo.py", tmp_path)
    assert "Alpha module registry demo" in out
    assert "optional_missing" in out


def test_alpha_cycle_status_demo_runs(tmp_path):
    out = _run("run_alpha_cycle_status_demo.py", tmp_path)
    assert "Alpha cycle status demo" in out
    assert "fix_blockers" in out


def test_alpha_report_demo_runs(tmp_path):
    out = _run("run_alpha_report_demo.py", tmp_path)
    assert "Alpha report demo" in out
    assert "No consciousness/life/agency claim is made." in out
