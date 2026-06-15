"""The five developmental-life demos run bounded and terminate."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

EXAMPLES = (
    "run_developmental_life_demo.py",
    "run_developmental_epoch_demo.py",
    "run_plateau_detection_demo.py",
    "run_regression_detection_demo.py",
    "run_growth_vs_accumulation_demo.py",
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
        capture_output=True, text=True, timeout=180, env=_env(), cwd=_ROOT)
    assert proc.returncode == 0, proc.stderr[-2000:]


def test_demo_disclaims_life_and_consciousness(tmp_path):
    path = os.path.join(_ROOT, "examples", "run_developmental_life_demo.py")
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", str(tmp_path / "out")],
        capture_output=True, text=True, timeout=180, env=_env(), cwd=_ROOT)
    out = (proc.stdout + proc.stderr).lower()
    assert "not a claim of biological life" in out or \
        "operational long-horizon" in out
