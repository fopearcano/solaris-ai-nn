"""Live birth examples run end to end without hanging."""

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


def test_init_demo_runs(tmp_path):
    out = _run("run_live_birth_init_demo.py", tmp_path)
    assert "Live birth init demo" in out
    assert "SAFE-OFF" in out


def test_doctor_demo_runs(tmp_path):
    out = _run("run_live_birth_doctor_demo.py", tmp_path)
    assert "Live birth doctor demo" in out
    assert "passed=True" in out


def test_validation_demo_runs(tmp_path):
    out = _run("run_live_birth_event_validation_demo.py", tmp_path)
    assert "Live event validation demo" in out
    assert "quarantined" in out.lower()


def test_live_birth_demo_runs(tmp_path):
    out = _run("run_live_birth_demo.py", tmp_path, ["--max-events", "50"])
    assert "Live read-only birth demo" in out
    assert "starts feeders/net  : False / False" in out


def test_certificate_demo_runs(tmp_path):
    out = _run("run_birth_certificate_demo.py", tmp_path)
    assert "Birth certificate demo" in out
    assert "does not imply consciousness" in out.lower()
