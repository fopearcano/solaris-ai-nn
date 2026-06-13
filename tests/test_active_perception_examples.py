"""Subprocess tests for the active perception examples."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def _run(script, *args, timeout=300):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
    assert time.perf_counter() - start < timeout, f"{script}: no infinite loop"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_active_perception_demo_runs(tmp_path):
    out = _run("run_active_perception_demo.py", "--steps", "120",
               "--state-dir", str(tmp_path / "s"))
    assert "regulating its own exposure" in out
    assert "sampling policy mode:" in out
    assert "claim guard safe: True" in out
    assert "no real-world autonomy" in out
    assert (tmp_path / "s" / "active_perception_report.md").exists()


def test_uncertainty_sampling_demo_runs(tmp_path):
    out = _run("run_uncertainty_sampling_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "target the weakest region" in out
    assert "prediction before:" in out
    assert "prediction after:" in out
    assert "claim guard safe: True" in out


def test_curiosity_safety_demo_runs(tmp_path):
    out = _run("run_curiosity_safety_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "safety always wins" in out
    assert "curiosity suppressed by safety:   True" in out
    assert "emergency decision:               no_sampling_action" in out
    assert "claim guard safe: True" in out


def test_stagnation_recovery_demo_runs(tmp_path):
    out = _run("run_stagnation_recovery_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "sample when the world is flat" in out
    assert "stagnation status:" in out
    assert "claim guard safe: True" in out


def test_proto_symbol_disambiguation_demo_runs(tmp_path):
    out = _run("run_proto_symbol_disambiguation_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "sample to test a sign" in out
    assert "ambiguity before:" in out
    assert "ambiguity after:" in out
    assert "claim guard safe: True" in out
