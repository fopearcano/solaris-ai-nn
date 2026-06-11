"""Subprocess tests for the communication examples."""

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


def test_operator_dialogue_demo_runs(tmp_path):
    out = _run("run_operator_dialogue_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=120)
    assert "interface, not authority" in out
    assert "[status]" in out
    assert "[unsafe_refusal]" in out
    assert "[emergency]" in out
    assert "grounded response ratio: 1.0" in out
    assert (tmp_path / "s" / "operator_transcript.jsonl").exists()


def test_communication_safety_demo_runs(tmp_path):
    out = _run("run_communication_safety_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "unsafe shell command" in out
    assert "REFUSED" in out
    assert "executed: False" in out
    assert "unsafe requests logged: 4" in out
    assert "nothing" in out.lower() and "executed" in out.lower()


def test_approval_dialogue_demo_runs(tmp_path):
    out = _run("run_governance_approval_dialogue_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "Approval recorded" in out
    assert "Rejection recorded" in out
    assert "cannot be decided" in out          # expired refusal
    assert "No pending approval request" in out  # unknown refusal
    assert "approvals processed: 1" in out


def test_report_demo_runs(tmp_path):
    out = _run("run_operator_report_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "generate self-report" in out
    assert "claim guard safe: True" in out
    assert "claim guard re-scan of saved Markdown: True" in out
    assert (tmp_path / "s" / "operator_self_report.md").exists()
