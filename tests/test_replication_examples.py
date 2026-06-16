"""Replication examples run bounded (no infinite loop) with expected output."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(example, state_dir, timeout=120):
    path = os.path.join(_ROOT, "examples", example)
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", state_dir],
        capture_output=True, text=True, timeout=timeout, cwd=_ROOT)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_registry_demo_runs(tmp_path):
    out = _run("run_replication_registry_demo.py", str(tmp_path / "reg"))
    assert "Replication registry demo" in out
    assert "registered runs" in out


def test_cross_run_alignment_demo_runs(tmp_path):
    out = _run("run_cross_run_alignment_demo.py", str(tmp_path / "al"))
    assert "Cross-run alignment demo" in out
    assert "inconclusive" in out


def test_structural_similarity_demo_runs(tmp_path):
    out = _run("run_structural_similarity_demo.py", str(tmp_path / "sim"))
    assert "Structural similarity demo" in out
    assert "fixture-overfit" in out


def test_falsification_lab_demo_runs(tmp_path):
    out = _run("run_falsification_lab_demo.py", str(tmp_path / "fl"))
    assert "Falsification lab demo" in out
    assert "passive_parser_comparison" in out


def test_replication_matrix_demo_runs(tmp_path):
    out = _run("run_replication_matrix_demo.py", str(tmp_path / "mx"))
    assert "Replication matrix demo" in out
    assert "falsified" in out
