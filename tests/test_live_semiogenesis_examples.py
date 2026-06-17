"""Live semiogenesis examples run end to end without hanging."""

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


def test_semiogenesis_demo_runs(tmp_path):
    out = _run("run_live_semiogenesis_demo.py", tmp_path)
    assert "First live semiogenesis demo" in out
    assert "cognition / signs=lang : False / False" in out


def test_sign_generator_demo_runs(tmp_path):
    out = _run("run_live_sign_generator_demo.py", tmp_path)
    assert "Live sign generator demo" in out
    assert "deterministic" in out


def test_sign_utility_demo_runs(tmp_path):
    out = _run("run_live_sign_utility_demo.py", tmp_path)
    assert "Live sign utility demo" in out
    assert "utility=" in out


def test_private_syntax_demo_runs(tmp_path):
    out = _run("run_live_private_syntax_demo.py", tmp_path)
    assert "Live private syntax demo" in out
    assert "relations" in out


def test_sign_birth_gate_demo_runs(tmp_path):
    out = _run("run_live_sign_birth_gate_demo.py", tmp_path)
    assert "Live sign birth gate demo" in out
    assert "distinct gate statuses observed" in out
