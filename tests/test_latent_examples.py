"""Subprocess tests for the latent cognition examples."""

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


def test_latent_replay_demo_runs(tmp_path):
    out = _run("run_latent_replay_demo.py", "--steps", "120",
               "--state-dir", str(tmp_path / "s"))
    assert "mode now:            awake" in out
    assert "production mutation: 0" in out
    assert (tmp_path / "s" / "latent_report.md").exists()


def test_sleep_cycle_demo_runs(tmp_path):
    out = _run("run_sleep_cycle_demo.py", "--steps", "120",
               "--state-dir", str(tmp_path / "s"))
    assert "-> sleep" in out
    assert "wake_transition -> awake" in out
    assert "wake transition summary:" in out
    assert "not\nhuman sleep" in out or "not human sleep" in out


def test_counterfactual_dream_demo_runs(tmp_path):
    out = _run("run_counterfactual_dream_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "production untouched:  True" in out
    assert "production mutations:  0" in out
    assert "claim guard safe: True" in out


def test_mysterium_anticipation_demo_runs(tmp_path):
    out = _run("run_mysterium_anticipation_demo.py", "--steps", "150",
               "--state-dir", str(tmp_path / "s"))
    assert "phase 1 (predictable" in out
    assert "phase 2 (surprising" in out
    assert "nothing mystical" in out
    # The story holds: accuracy drops, pressure rises.
    lines = out.splitlines()
    accuracies = [float(l.split(":")[1]) for l in lines
                  if "rolling accuracy:" in l]
    pressures = [float(l.split(":")[1].split()[0]) for l in lines
                 if "unknown pressure:" in l]
    assert accuracies[1] < accuracies[0]
    assert pressures[1] > pressures[0]
