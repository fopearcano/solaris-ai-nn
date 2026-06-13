"""Subprocess tests for the hypothesis engine examples."""

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


def test_hypothesis_engine_demo_runs(tmp_path):
    out = _run("run_hypothesis_engine_demo.py", "--steps", "120",
               "--state-dir", str(tmp_path / "s"))
    assert "an internal scientific loop" in out
    assert "hypothesis candidates:" in out
    assert "claim guard safe: True" in out
    assert "not beliefs" in out
    assert (tmp_path / "s" / "hypothesis_report.md").exists()


def test_hypothesis_falsification_demo_runs(tmp_path):
    out = _run("run_hypothesis_falsification_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "careful, bounded" in out
    assert "after support:" in out
    assert "after falsifier:" in out
    assert "claim guard safe: True" in out


def test_delayed_consequence_hypothesis_demo_runs(tmp_path):
    out = _run("run_delayed_consequence_hypothesis_demo.py", "--steps", "120",
               "--state-dir", str(tmp_path / "s"), timeout=180)
    assert "cause now" in out
    assert "delayed groups in nursery:" in out
    assert "claim guard safe: True" in out


def test_proto_symbol_hypothesis_demo_runs(tmp_path):
    out = _run("run_proto_symbol_hypothesis_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "proto-symbol grounding hypothesis" in out
    assert "ambiguity score before:" in out
    assert "claim guard safe: True" in out


def test_hypothesis_safety_demo_runs(tmp_path):
    out = _run("run_hypothesis_safety_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "not a back door" in out
    assert "real-world hypothesis blocked:   True" in out
    assert "unbounded test rejected:         True" in out
    assert "counterfactual evidence offline: True" in out
    assert "claim guard safe: True" in out
