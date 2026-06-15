"""The five perceptual-metabolism demos run bounded and terminate."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

EXAMPLES = (
    "run_perceptual_metabolism_demo.py",
    "run_sensory_overload_demo.py",
    "run_sensory_deprivation_demo.py",
    "run_source_diet_demo.py",
    "run_consolidation_pressure_demo.py",
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("script", EXAMPLES)
def test_example_runs_bounded(script, tmp_path):
    path = os.path.join(_ROOT, "examples", script)
    assert os.path.isfile(path), path
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(_ROOT, "src") + os.pathsep + \
        env.get("PYTHONPATH", "")
    # A short timeout guarantees the demo is bounded (no infinite loop).
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", str(tmp_path / script)],
        capture_output=True, text=True, timeout=120, env=env, cwd=_ROOT)
    assert proc.returncode == 0, proc.stderr[-2000:]


def test_demo_output_disclaims_feelings_and_life(tmp_path):
    path = os.path.join(_ROOT, "examples", "run_perceptual_metabolism_demo.py")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(_ROOT, "src") + os.pathsep + \
        env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", str(tmp_path / "out")],
        capture_output=True, text=True, timeout=120, env=env, cwd=_ROOT)
    out = (proc.stdout + proc.stderr).lower()
    # The demo never claims feelings, life, or consciousness.
    assert "not feelings" in out or "operational" in out
