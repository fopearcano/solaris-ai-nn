"""Compiler examples run bounded (no infinite loop) with expected output."""

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


def test_compiler_demo_runs(tmp_path):
    out = _run("run_experiment_compiler_demo.py", str(tmp_path / "c"))
    assert "Experiment compiler demo" in out
    assert "creates branch        : False" in out


def test_prompt_pack_demo_runs(tmp_path):
    out = _run("run_prompt_pack_demo.py", str(tmp_path / "pp"))
    assert "Prompt pack demo" in out
    assert "hard prohibitions" in out


def test_branch_spec_demo_runs(tmp_path):
    out = _run("run_branch_spec_demo.py", str(tmp_path / "bs"))
    assert "Branch spec demo" in out
    assert "branch created        : False" in out


def test_safety_gate_demo_runs(tmp_path):
    out = _run("run_safety_gate_compiler_demo.py", str(tmp_path / "sg"))
    assert "Safety gate compiler demo" in out
    assert "blocked_by_safety" in out


def test_review_packet_demo_runs(tmp_path):
    out = _run("run_operator_review_packet_demo.py", str(tmp_path / "rp"))
    assert "Operator review packet demo" in out
    assert "self-approved = False" in out
