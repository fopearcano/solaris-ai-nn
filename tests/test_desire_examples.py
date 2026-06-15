"""The five desire-formation demos run bounded and terminate."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

EXAMPLES = (
    "run_desire_formation_demo.py",
    "run_desire_conflict_demo.py",
    "run_internal_action_readiness_demo.py",
    "run_no_action_arbitration_demo.py",
    "run_safety_blocked_desire_demo.py",
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(_ROOT, "src") + os.pathsep + \
        env.get("PYTHONPATH", "")
    return env


@pytest.mark.parametrize("script", EXAMPLES)
def test_example_runs_bounded(script, tmp_path):
    path = os.path.join(_ROOT, "examples", script)
    assert os.path.isfile(path), path
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", str(tmp_path / script)],
        capture_output=True, text=True, timeout=120, env=_env(), cwd=_ROOT)
    assert proc.returncode == 0, proc.stderr[-2000:]


def test_demo_disclaims_emotion_and_agency(tmp_path):
    path = os.path.join(_ROOT, "examples", "run_desire_formation_demo.py")
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", str(tmp_path / "out")],
        capture_output=True, text=True, timeout=120, env=_env(), cwd=_ROOT)
    out = (proc.stdout + proc.stderr).lower()
    assert "not emotions" in out or "operational pressures toward internal" in out
