"""Subprocess tests for the LOGOS examples."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def _run(script, *args, timeout=180):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
    assert time.perf_counter() - start < timeout, f"{script}: no infinite loop"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_fracture_demo_runs(tmp_path):
    out = _run("run_logos_fracture_demo.py", "--state-dir", str(tmp_path / "s"))
    assert "tension is productive pressure" in out
    assert "tensions detected:" in out
    assert "claim guard safe: True" in out
    assert "not an authority" in out


def test_synthesis_demo_runs(tmp_path):
    out = _run("run_logos_synthesis_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "proposed, not assumed true" in out
    assert "synthesis candidates:" in out
    assert "claim guard safe: True" in out


def test_complexity_regulation_demo_runs(tmp_path):
    out = _run("run_complexity_regulation_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "inert / productive / overloaded" in out
    assert "overloaded" in out
    assert "not a consciousness or life score" in out


def test_esc_process_demo_runs(tmp_path):
    out = _run("run_esc_process_demo.py", "--state-dir", str(tmp_path / "s"))
    assert "instability signal, not emotion" in out
    assert "triggered=True" in out
    assert "claim guard safe: True" in out


def test_logos_safety_demo_runs(tmp_path):
    out = _run("run_logos_safety_demo.py", "--state-dir", str(tmp_path / "s"))
    assert "not a back door" in out
    assert "source-code synthesis blocked:    True" in out
    assert "destructive evidence merge blocked:  True" in out
    assert "claim guard safe: True" in out
