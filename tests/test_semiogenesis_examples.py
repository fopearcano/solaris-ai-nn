"""The five semiogenesis demos run bounded and terminate."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

EXAMPLES = (
    "run_semiogenesis_demo.py",
    "run_sign_birth_utility_demo.py",
    "run_private_syntax_demo.py",
    "run_sign_drift_demo.py",
    "run_gloss_contamination_demo.py",
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


def test_demo_disclaims_words(tmp_path):
    path = os.path.join(_ROOT, "examples", "run_semiogenesis_demo.py")
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", str(tmp_path / "out")],
        capture_output=True, text=True, timeout=120, env=_env(), cwd=_ROOT)
    out = (proc.stdout + proc.stderr).lower()
    assert "not human words" in out or "operational markers" in out
